from app.presentation.api_router import api_router


def test_blueprint_route_aliases_are_exposed() -> None:
    paths = {route.path for route in api_router.routes}

    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/users" in paths
    assert "/users/create" in paths
    assert "/users/list" in paths
    assert "/diagnostic/start" in paths
    assert "/diagnostic/submit" in paths
    assert "/diagnostic/complete" in paths
    assert "/roadmap/generate" in paths
    assert "/roadmap/view" in paths
