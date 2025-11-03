import asyncio
import logging
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Coroutine, Iterable, Optional

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    RoomInputOptions,
    RoomIO,
    RoomOutputOptions,
    StopResponse,
    llm,
    utils,
)
from livekit.plugins import openai, silero
from meshagent.api import MeshDocument, SchemaRegistration, SchemaRegistry
from meshagent.agents import SingleRoomAgent
from meshagent.tools import RemoteToolkit, ToolContext, Tool
from meshagent.api.room_server_client import Requirement
from meshagent.livekit.agents.voice import VoiceConnection
from meshagent.agents.schemas.transcript import transcript_schema

logger = logging.getLogger("meeting_transcriber")

_shared_vad = None


@dataclass
class TranscriptSession:
    document: MeshDocument

    def append_segment(
        self,
        *,
        participant_name: str,
        text: str,
        participant_id: Optional[str] = None,
        time: Optional[str] = None,
    ) -> bool:
        normalized_text = (text or "").strip()
        if not normalized_text:
            return False

        normalized_name = (participant_name or "").strip()
        alias_set: set[str] = set()
        if normalized_name:
            alias_set.add(normalized_name)
        if participant_id:
            alias_set.add(str(participant_id).strip())
        alias_set = {a for a in alias_set if a}
        if not alias_set:
            alias_set.add("")

        payload = {"participant_name": normalized_name, "text": normalized_text}
        if participant_id:
            payload["participant_id"] = participant_id
        if time:
            payload["time"] = time

        self.document.root.append_child("segment", payload)
        return True


def _get_shared_vad():
    global _shared_vad
    if _shared_vad is None:
        _shared_vad = silero.VAD.load()
    return _shared_vad


class _ParticipantTranscriber(Agent):
    def __init__(
        self,
        *,
        participant_name: str,
        participant_id: Optional[str],
        on_transcript: Optional[Callable[..., Awaitable[None]]] = None,
    ):
        super().__init__(
            instructions="not-needed",
            stt=openai.STT(),
        )
        self._participant_name = participant_name or "unknown participant"
        self._participant_id = participant_id
        self._on_transcript = on_transcript

    async def on_user_turn_completed(
        self, chat_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ):
        user_transcript = new_message.text_content
        logger.info("%s -> %s", self._participant_name, user_transcript)
        await self._on_transcript(
            participant_id=self._participant_id,
            participant_name=self._participant_name,
            chat_ctx=chat_ctx,
            new_message=new_message,
        )
        raise StopResponse()


class _MeetingManager:
    def __init__(
        self,
        *,
        room: rtc.Room,
        vad,
        on_transcript: Optional[Callable[..., Awaitable[None]]] = None,
    ):
        self.room = room
        self._vad = vad
        self._sessions: dict[str, AgentSession] = {}
        self._tasks: set[asyncio.Task] = set()
        self._closed = False
        self._on_transcript = on_transcript

    @staticmethod
    def _resolve_participant_identity(
        participant: rtc.RemoteParticipant,
    ) -> tuple[str, Optional[str]]:
        return (
            participant.name,
            participant.identity,
        )

    def start(self):
        self.room.on("participant_connected", self.on_participant_connected)
        self.room.on("participant_disconnected", self.on_participant_disconnected)

    async def aclose(self):
        self._closed = True
        await utils.aio.cancel_and_wait(*self._tasks)

        await asyncio.gather(
            *[self._close_session(session) for session in self._sessions.values()]
        )

        self.room.off("participant_connected", self.on_participant_connected)
        self.room.off("participant_disconnected", self.on_participant_disconnected)

    def on_participant_connected(self, participant: rtc.RemoteParticipant):
        if participant.identity in self._sessions:
            return

        if self._closed:
            logger.debug(
                "ignoring connect for %s because transcriber is closed",
                getattr(participant, "identity", None),
            )
            return

        readable_name, participant_id = self._resolve_participant_identity(participant)
        kind = getattr(participant, "kind", None)
        logger.info("participant connected: %s (kind=%s)", readable_name, kind)

        task = asyncio.create_task(self._start_session(participant))
        self._tasks.add(task)

        def on_task_done(task: asyncio.Task):
            try:
                self._sessions[participant.identity] = task.result()
            finally:
                self._tasks.discard(task)

        task.add_done_callback(on_task_done)

    def on_participant_disconnected(self, participant: rtc.RemoteParticipant):
        readable_name, participant_id = self._resolve_participant_identity(participant)
        logger.info("participant disconnected: %s", readable_name)
        session = self._sessions.pop(participant.identity, None)
        if session is None:
            return

        logger.info("closing session for %s", participant_id or readable_name)
        task = asyncio.create_task(self._close_session(session))
        self._tasks.add(task)
        task.add_done_callback(lambda _: self._tasks.discard(task))

    async def _start_session(self, participant: rtc.RemoteParticipant) -> AgentSession:
        if participant.identity in self._sessions:
            return self._sessions[participant.identity]

        display_name, participant_id = self._resolve_participant_identity(participant)
        logger.debug("creating session for %s (id=%s)", display_name, participant_id)

        session = AgentSession(
            vad=self._vad,
        )

        room_io = RoomIO(
            agent_session=session,
            room=self.room,
            participant=participant,
            input_options=RoomInputOptions(
                # text input is not supported for multiple room participants
                # if needed, register the text stream handler by yourself
                # and route the text to different sessions based on the participant identity
                text_enabled=False,
            ),
            output_options=RoomOutputOptions(
                transcription_enabled=True,
                audio_enabled=False,
            ),
        )
        await room_io.start()
        agent = _ParticipantTranscriber(
            participant_name=display_name,
            participant_id=participant_id,
            on_transcript=self._on_transcript,
        )
        await session.start(agent=agent)
        return session

    async def _close_session(self, sess: AgentSession) -> None:
        await sess.drain()
        await sess.aclose()


SessionKey = tuple[str, str]


@dataclass
class _SessionState:
    breakout_room: Optional[str]
    transcript_path: str
    voice_conn: VoiceConnection
    manager: _MeetingManager


class StartTranscriptionTool(Tool):
    def __init__(self, *, transcriber: "MeetingTranscriber"):
        self.transcriber = transcriber
        super().__init__(
            name="start_transcription",
            input_schema={
                "type": "object",
                "required": [
                    "breakout_room",
                    "path",
                ],
                "additionalProperties": False,
                "properties": {
                    "breakout_room": {
                        "type": "string",
                    },
                    "path": {
                        "type": "string",
                    },
                },
            },
        )

    async def execute(self, context: ToolContext, *, breakout_room: str, path: str):
        await self.transcriber.start_transcription(
            breakout_room=breakout_room, path=path
        )
        return {"status": "started"}


class StopTranscriptionTool(Tool):
    def __init__(self, *, transcriber: "MeetingTranscriber"):
        self.transcriber = transcriber
        super().__init__(
            name="stop_transcription",
            input_schema={
                "type": "object",
                "required": [
                    "breakout_room",
                    "path",
                ],
                "additionalProperties": False,
                "properties": {
                    "breakout_room": {
                        "type": "string",
                    },
                    "path": {
                        "type": "string",
                    },
                },
            },
        )

    async def execute(self, context: ToolContext, *, breakout_room: str, path: str):
        await self.transcriber.stop_transcription(
            breakout_room=breakout_room, path=path
        )
        return {"status": "stopped"}


class MeetingTranscriber(SingleRoomAgent):
    _STATUS_ATTRIBUTE_KEY = "transcriber_status"

    def __init__(self, name: str, requires: Optional[list[Requirement]] = None):
        super().__init__(
            name=name,
            requires=requires,
        )
        self._sessions: dict[SessionKey, _SessionState] = {}
        self._pending_sessions: set[SessionKey] = set()
        self._transcript_sessions: dict[str, TranscriptSession] = {}
        self._status_entries: dict[SessionKey, dict[str, Any]] = {}
        self._tasks: set[asyncio.Task] = set()
        self._session_tasks_by_key: dict[SessionKey, asyncio.Task] = {}
        self._deferred_stop_keys: set[SessionKey] = set()
        self._deferred_stop_reasons: dict[SessionKey, str] = {}
        self._session_lock = asyncio.Lock()
        self._toolkit = RemoteToolkit(
            name="transcription",
            tools=[
                StartTranscriptionTool(transcriber=self),
                StopTranscriptionTool(transcriber=self),
            ],
        )

    @staticmethod
    def _make_session_key(breakout_room: str, transcript_path: str) -> SessionKey:
        return (breakout_room, transcript_path)

    def _sessions_using_path(self, path: str) -> int:
        return sum(
            1 for session in self._sessions.values() if session.transcript_path == path
        )

    async def _publish_status_attribute(self) -> None:
        if not getattr(self, "room", None):
            return
        payload: dict[str, dict[str, Any]] = {}
        for key in sorted(self._status_entries):
            entry = self._status_entries[key]
            breakout_room, transcript_path = key
            entry_payload = dict(entry)
            entry_payload.pop("breakout_room", None)
            breakout_bucket = payload.setdefault(breakout_room, {})
            breakout_bucket[transcript_path] = entry_payload
        try:
            await self.room.local_participant.set_attribute(
                self._STATUS_ATTRIBUTE_KEY,
                payload,
            )
        except (
            Exception
        ) as exc:  # pragma: no cover - attribute updates should not break flow
            logger.warning(
                "failed to update transcriber status attribute: %s", exc, exc_info=exc
            )

    async def _update_status_entry(
        self,
        session_key: SessionKey,
        *,
        state: str,
        breakout_room: Optional[str],
        transcript_path: str,
        reason: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        entry = dict(self._status_entries.get(session_key, {}))
        now = datetime.utcnow().isoformat() + "Z"
        if "created_at" not in entry:
            entry["created_at"] = now
        entry.update(
            {
                "session_id": f"{session_key[0]}::{session_key[1]}",
                "state": state,
                "active": state == "active",
                "breakout_room": breakout_room,
                "transcript_path": transcript_path,
                "updated_at": now,
            }
        )
        if reason is not None:
            entry["reason"] = reason
        else:
            entry.pop("reason", None)
        if error is not None:
            entry["error"] = error
        else:
            entry.pop("error", None)
        self._status_entries[session_key] = entry
        await self._publish_status_attribute()

    async def _remove_status_entry(self, session_key: SessionKey) -> None:
        if session_key in self._status_entries:
            self._status_entries.pop(session_key, None)
            await self._publish_status_attribute()

    def _spawn_task(
        self,
        coro: Coroutine[Any, Any, Any],
        *,
        session_key: Optional[SessionKey] = None,
    ) -> None:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        if session_key is not None:
            self._session_tasks_by_key[session_key] = task

        def _on_done(t: asyncio.Task):
            self._tasks.discard(t)
            if session_key is not None:
                self._session_tasks_by_key.pop(session_key, None)
            try:
                t.result()
            except asyncio.CancelledError:
                logger.debug("transcriber task cancelled")
            except Exception as exc:
                logger.error("transcriber task failed: %s", exc, exc_info=exc)

        task.add_done_callback(_on_done)

    @staticmethod
    def _default_transcript_document_path() -> str:
        env_path = os.getenv("TRANSCRIPT_DOCUMENT_PATH", "").strip()
        return env_path or "transcript.transcript"

    async def _release_transcript_session(self, path: str) -> None:
        ts = self._transcript_sessions.pop(path, None)
        if not ts:
            return
        doc = ts.document
        close_coro = getattr(doc, "aclose", None)
        if callable(close_coro):
            try:
                await close_coro()
                return
            except Exception as exc:
                logger.debug(
                    "failed to aclose transcript document: %s", exc, exc_info=exc
                )
        close_fn = getattr(doc, "close", None)
        if callable(close_fn):
            try:
                maybe = close_fn()
                if asyncio.iscoroutine(maybe):
                    await maybe
            except Exception as exc:
                logger.debug(
                    "failed to close transcript document: %s", exc, exc_info=exc
                )

    async def _ensure_transcript_session(self, path: str) -> TranscriptSession:
        session = self._transcript_sessions.get(path)
        if session is None:
            doc = await self.room.sync.open(path=path, create=True)
            session = TranscriptSession(document=doc)
            self._transcript_sessions[path] = session
            logger.info("transcript document ready at %s", path)
        return session

    async def start(self, *, room):
        await super().start(room=room)
        await self._toolkit.start(room=room)
        await room.local_participant.set_attribute("supports_voice", True)
        await room.messaging.enable()
        await self._publish_status_attribute()

    async def start_transcription(self, *, breakout_room: Optional[str], path: str):
        session_key = self._make_session_key(breakout_room, path)
        if session_key in self._sessions or session_key in self._pending_sessions:
            logger.warning(
                "start_transcription for breakout=%s transcript=%s ignored; session already active or pending",
                breakout_room,
                path,
            )
            return
        logger.info(
            "transcription starting (breakout=%s transcript=%s)",
            breakout_room,
            path,
        )
        self._spawn_task(
            self._start_transcription_session(
                session_key=session_key,
                breakout_room=breakout_room,
                transcript_path=path,
            ),
            session_key=session_key,
        )

    async def stop_transcription(self, *, breakout_room: Optional[str], path: str):
        breakout_filter = breakout_room if breakout_room is not None else None
        target_keys = self._find_session_keys(breakout_filter, path)
        if not target_keys:
            logger.warning(
                "stop_transcription received but no matching sessions (breakout=%s transcript=%s)",
                breakout_room,
                path,
            )
            return
        logger.info(
            "stop_transcription received (breakout=%s transcript=%s); stopping %d session(s)",
            breakout_room,
            path,
            len(target_keys),
        )
        for key in target_keys:
            if key in self._sessions:
                self._spawn_task(
                    self._stop_transcription_session(
                        session_key=key, reason="stop_transcription"
                    )
                )
            elif key in self._pending_sessions:
                self._deferred_stop_keys.add(key)
                self._deferred_stop_reasons[key] = "stop_transcription"
                entry = self._status_entries.get(key)
                if entry:
                    self._spawn_task(
                        self._update_status_entry(
                            key,
                            state="closing",
                            breakout_room=entry["breakout_room"],
                            transcript_path=entry["transcript_path"],
                            reason="stop_transcription",
                        )
                    )
            else:
                entry = self._status_entries.get(key)
                if entry:
                    self._spawn_task(
                        self._update_status_entry(
                            key,
                            state="closing",
                            breakout_room=entry["breakout_room"],
                            transcript_path=entry["transcript_path"],
                            reason="stop_transcription",
                        )
                    )

    def _find_session_keys(
        self,
        breakout_room: Optional[str],
        transcript_path: Optional[str],
    ) -> list[SessionKey]:
        matches: list[SessionKey] = []
        for key, entry in self._status_entries.items():
            if breakout_room is not None and key[0] != breakout_room:
                continue
            if (
                transcript_path is not None
                and entry.get("transcript_path") != transcript_path
            ):
                continue
            matches.append(key)
        return matches

    async def _start_transcription_session(
        self,
        *,
        session_key: SessionKey,
        breakout_room: Optional[str],
        transcript_path: str,
    ) -> None:
        async with self._session_lock:
            if session_key in self._sessions or session_key in self._pending_sessions:
                return
            self._pending_sessions.add(session_key)

        await self._update_status_entry(
            session_key,
            state="connecting",
            breakout_room=breakout_room,
            transcript_path=transcript_path,
        )

        voice_conn: Optional[VoiceConnection] = None
        manager: Optional[_MeetingManager] = None

        try:
            voice_conn = VoiceConnection(room=self.room, breakout_room=breakout_room)
            logger.info(
                "joining breakout %s (transcript=%s)",
                breakout_room,
                transcript_path,
            )
            await voice_conn.__aenter__()

            livekit_room = voice_conn.livekit_room
            if livekit_room is None:
                raise RuntimeError("VoiceConnection did not return a LiveKit room")

            await self._ensure_transcript_session(transcript_path)

            async def _handle_transcript(
                participant_id: str,
                participant_name: str,
                chat_ctx: llm.ChatContext,
                new_message: llm.ChatMessage,
            ):
                ts = await self._ensure_transcript_session(transcript_path)
                stored = ts.append_segment(
                    participant_name=participant_name,
                    text=new_message.text_content,
                    participant_id=participant_id,
                    time=datetime.utcnow().isoformat() + "Z",
                )
                if not stored:
                    logger.debug(
                        "duplicate transcript skipped for %s", participant_name
                    )

            manager = _MeetingManager(
                room=livekit_room,
                vad=_get_shared_vad(),
                on_transcript=_handle_transcript,
            )
            manager.start()

            remotes = getattr(livekit_room, "remote_participants", None) or ()
            if isinstance(remotes, dict):
                participant_iter: Iterable[rtc.RemoteParticipant] = remotes.values()
            else:
                participant_iter = remotes

            participants = [p for p in participant_iter if p is not None]

            for participant in participants:
                try:
                    manager.on_participant_connected(participant)
                except Exception as exc:
                    logger.error(
                        "failed starting session for %s: %s",
                        getattr(participant, "identity", "?"),
                        exc,
                        exc_info=exc,
                    )

            session_state = _SessionState(
                breakout_room=breakout_room,
                transcript_path=transcript_path,
                voice_conn=voice_conn,
                manager=manager,
            )

            async with self._session_lock:
                self._sessions[session_key] = session_state
                self._pending_sessions.discard(session_key)

            await self._update_status_entry(
                session_key,
                state="active",
                breakout_room=breakout_room,
                transcript_path=transcript_path,
            )

        except asyncio.CancelledError:
            async with self._session_lock:
                self._pending_sessions.discard(session_key)
                self._sessions.pop(session_key, None)
            if manager:
                try:
                    await manager.aclose()
                except Exception as exc:
                    logger.error(
                        "failed closing cancelled transcriber: %s", exc, exc_info=exc
                    )
            if voice_conn:
                try:
                    await voice_conn.__aexit__(None, None, None)
                except Exception as exc:
                    logger.error(
                        "failed disconnecting cancelled livekit: %s", exc, exc_info=exc
                    )
            if self._sessions_using_path(transcript_path) == 0:
                await self._release_transcript_session(transcript_path)
            await self._update_status_entry(
                session_key,
                state="cancelled",
                breakout_room=breakout_room,
                transcript_path=transcript_path,
                reason="cancelled",
            )
            raise
        except Exception as exc:
            async with self._session_lock:
                self._pending_sessions.discard(session_key)
                self._sessions.pop(session_key, None)
            if manager:
                try:
                    await manager.aclose()
                except Exception as close_exc:
                    logger.error(
                        "failed closing multi-user transcriber: %s",
                        close_exc,
                        exc_info=close_exc,
                    )
            if voice_conn:
                try:
                    await voice_conn.__aexit__(None, None, None)
                except Exception as disconnect_exc:
                    logger.error(
                        "failed disconnecting livekit: %s",
                        disconnect_exc,
                        exc_info=disconnect_exc,
                    )
            if self._sessions_using_path(transcript_path) == 0:
                await self._release_transcript_session(transcript_path)
            await self._update_status_entry(
                session_key,
                state="error",
                breakout_room=breakout_room,
                transcript_path=transcript_path,
                error=str(exc),
            )
            raise
        else:
            logger.info(
                "ready to transcribe breakout=%s transcript=%s (participants=%d)",
                breakout_room,
                transcript_path,
                len(participants),
            )
            if session_key in self._deferred_stop_keys:
                reason = self._deferred_stop_reasons.pop(session_key, "stop_requested")
                self._deferred_stop_keys.discard(session_key)
                self._spawn_task(
                    self._stop_transcription_session(
                        session_key=session_key, reason=reason
                    )
                )
        finally:
            async with self._session_lock:
                self._pending_sessions.discard(session_key)

    async def _stop_transcription_session(
        self,
        *,
        session_key: SessionKey,
        reason: str,
        suppress_log: bool = False,
    ) -> None:
        async with self._session_lock:
            session = self._sessions.pop(session_key, None)

        if not session:
            await self._remove_status_entry(session_key)
            return

        breakout_room = session.breakout_room
        transcript_path = session.transcript_path

        await self._update_status_entry(
            session_key,
            state="closing",
            breakout_room=breakout_room,
            transcript_path=transcript_path,
            reason=reason,
        )

        if session.manager:
            try:
                await session.manager.aclose()
            except Exception as exc:
                logger.error(
                    "failed closing multi-user transcriber: %s", exc, exc_info=exc
                )

        if session.voice_conn:
            try:
                await session.voice_conn.__aexit__(None, None, None)
            except Exception as exc:
                logger.error("failed disconnecting livekit: %s", exc, exc_info=exc)

        if self._sessions_using_path(transcript_path) == 0:
            await self._release_transcript_session(transcript_path)

        await self._remove_status_entry(session_key)
        self._deferred_stop_keys.discard(session_key)
        self._deferred_stop_reasons.pop(session_key, None)

        if not suppress_log:
            logger.info(
                "closed livekit connection (breakout=%s transcript=%s reason=%s)",
                breakout_room,
                transcript_path,
                reason,
            )

    async def _stop_all_sessions(self, *, reason: str) -> None:
        keys = list(self._sessions.keys())
        for key in keys:
            await self._stop_transcription_session(
                session_key=key, reason=reason, suppress_log=True
            )

        pending = list(self._pending_sessions)
        for key in pending:
            self._deferred_stop_keys.add(key)
            self._deferred_stop_reasons[key] = reason
            entry = self._status_entries.get(key)
            if entry:
                await self._update_status_entry(
                    key,
                    state="closing",
                    breakout_room=entry["breakout_room"],
                    transcript_path=entry["transcript_path"],
                    reason=reason,
                )
            task = self._session_tasks_by_key.get(key)
            if task:
                task.cancel()

    async def stop(self):
        await self._toolkit.stop()
        await self._stop_all_sessions(reason="agent_stop")
        if self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)
        self._status_entries.clear()
        await self._publish_status_attribute()
        await super().stop()


class TranscriptRegistry(SchemaRegistry):
    def __init__(self):
        name = "transcript"
        super().__init__(
            name=f"meshagent.schema.{name}",
            validate_webhook_secret=False,
            schemas=[SchemaRegistration(name=name, schema=transcript_schema)],
        )
