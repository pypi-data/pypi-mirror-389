# tests/entrypoints/test_di.py
from __future__ import annotations

import pytest

import scraper2_hj3415.di as mod
from scraper2_hj3415.core.usecases.c1034_ingest import C1034IngestUseCase


class DummyRepo:
    # C1034RepositoryPort를 따르는 더블(메서드가 실제 호출되지는 않음)
    pass


class FakePlaywrightSession:
    def __init__(self, *, headless: bool = True):
        self.headless = headless
        self.closed = False

    @classmethod
    async def create(cls, headless: bool = True):
        return cls(headless=headless)

    async def close(self):
        self.closed = True


class FakeNfsBundleSource:
    def __init__(self, session: FakePlaywrightSession):
        # DI가 session을 그대로 넘겨주는지 검사 용도
        self.session = session


class FakeC1034Sink:
    def __init__(self, repo: DummyRepo, chunk: int = 1000):
        # DI가 repo/chunk를 그대로 넘겨주는지 검사 용도
        self.repo = repo
        self.chunk = chunk


@pytest.fixture
def fakes(monkeypatch: pytest.MonkeyPatch):
    """
    di 모듈 내부에서 import한 어댑터들을 전부 페이크로 바꾼다.
    (실 브라우저/네트워크 호출 방지)
    """
    monkeypatch.setattr(mod, "PlaywrightSession", FakePlaywrightSession)
    monkeypatch.setattr(mod, "NfsBundleSource", FakeNfsBundleSource)
    monkeypatch.setattr(mod, "C1034Sink", FakeC1034Sink)
    yield


@pytest.mark.asyncio
async def test_provide_ingest_usecase_env_defaults_and_cleanup(fakes, monkeypatch):
    """
    - ENV가 없을 때 기본값(headless=True, chunk=1000) 사용
    - 생성된 UseCase 타입/구성 확인
    - 컨텍스트 종료 시 PlaywrightSession.close() 호출됨
    """
    # ENV 클린
    monkeypatch.delenv("SCRAPER_HEADLESS", raising=False)
    monkeypatch.delenv("SCRAPER_SINK_CHUNK", raising=False)

    repo = DummyRepo()

    # with 컨텍스트 안: UseCase가 조립되어야 함
    async with mod.provide_ingest_usecase(repo=repo) as uc:
        assert isinstance(uc, C1034IngestUseCase)

        # 내부 오브젝트 접근 (테스트 가독성을 위해 내부 속성 체크)
        # source는 FakeNfsBundleSource, sink는 FakeC1034Sink 이어야 한다
        assert isinstance(uc.source, FakeNfsBundleSource)
        assert isinstance(uc.sink, FakeC1034Sink)

        # 세션의 headless 기본값: True
        assert isinstance(uc.source.session, FakePlaywrightSession)
        assert uc.source.session.headless is True

        # chunk 기본값: 1000
        assert uc.sink.chunk == 1000

        # on_bundle은 None (기본)
        assert uc.on_bundle is None

        # 아직은 session이 닫히면 안 됨
        assert uc.source.session.closed is False

    # 컨텍스트 종료 후: 세션이 닫혀야 함
    assert uc.source.session.closed is True


@pytest.mark.asyncio
async def test_provide_ingest_usecase_env_overrides(fakes, monkeypatch):
    """
    - ENV로 headless, chunk를 오버라이드하면 해당 값으로 세팅되어야 함
    """
    monkeypatch.setenv("SCRAPER_HEADLESS", "false")
    monkeypatch.setenv("SCRAPER_SINK_CHUNK", "2048")

    repo = DummyRepo()
    async with mod.provide_ingest_usecase(repo=repo) as uc:
        assert isinstance(uc, C1034IngestUseCase)
        assert isinstance(uc.source.session, FakePlaywrightSession)
        assert uc.source.session.headless is False   # env 반영
        assert uc.sink.chunk == 2048                 # env 반영


@pytest.mark.asyncio
async def test_provide_ingest_usecase_params_override_env(fakes, monkeypatch):
    """
    - 함수 파라미터(headless, chunk)가 ENV보다 우선한다.
    """
    monkeypatch.setenv("SCRAPER_HEADLESS", "false")
    monkeypatch.setenv("SCRAPER_SINK_CHUNK", "2048")

    repo = DummyRepo()
    async with mod.provide_ingest_usecase(repo=repo, headless=True, chunk=4096) as uc:
        assert isinstance(uc, C1034IngestUseCase)
        assert uc.source.session.headless is True    # 파라미터 우선
        assert uc.sink.chunk == 4096                 # 파라미터 우선


@pytest.mark.asyncio
async def test_provide_ingest_usecase_on_bundle_passthrough(fakes):
    """
    - on_bundle 콜백이 UseCase에 그대로 세팅되는지 확인
    """
    async def on_bundle(page: str, bundle) -> None:
        pass

    repo = DummyRepo()
    async with mod.provide_ingest_usecase(repo=repo, on_bundle=on_bundle) as uc:
        assert uc.on_bundle is on_bundle


@pytest.mark.asyncio
async def test_provide_ingest_usecase_with_session_does_not_close_external_session(fakes):
    """
    - provide_ingest_usecase_with_session는 전달받은 session을 닫지 않아야 한다.
    - chunk는 ENV 또는 파라미터로 설정.
    """
    # 외부에서 세션을 준비했다고 가정
    external = FakePlaywrightSession(headless=False)

    repo = DummyRepo()
    async with mod.provide_ingest_usecase_with_session(session=external, repo=repo, chunk=256) as uc:
        assert isinstance(uc, C1034IngestUseCase)
        # 전달한 세션이 그대로 사용되는지
        assert uc.source.session is external
        assert uc.source.session.headless is False
        assert uc.sink.chunk == 256

    # 컨텍스트 종료 후에도 외부 세션은 닫지 않는다
    assert external.closed is False


@pytest.mark.asyncio
async def test_provide_ingest_usecase_with_session_env_chunk(fakes, monkeypatch):
    """
    - with_session 버전에서 chunk 파라미터 미지정 시 ENV 적용
    """
    monkeypatch.setenv("SCRAPER_SINK_CHUNK", "777")

    external = FakePlaywrightSession(headless=True)
    repo = DummyRepo()
    async with mod.provide_ingest_usecase_with_session(session=external, repo=repo) as uc:
        assert uc.sink.chunk == 777
    assert external.closed is False