from app.behavior import BehaviorDefinition

def test_behavior_definition():
    data = {"agents": [], "tasks": []}
    behavior = BehaviorDefinition(**data)
    assert behavior.agents == []