def test_plan_model_columns():
    from app.models import Plan
    cols = {c.name for c in Plan.__table__.columns}
    assert cols == {
        "id", "code", "name", "monthly_inr", "monthly_lead_quota", "features",
        "created_at", "updated_at",
    }
    assert Plan.__table__.c.code.unique is True


def test_organization_model_columns():
    from app.models import Organization
    cols = {c.name for c in Organization.__table__.columns}
    required = {
        "id", "name", "slug", "plan_id", "status",
        "default_language", "branding", "data_residency",
        "created_at", "updated_at",
    }
    assert required <= cols


def test_user_model_columns():
    from app.models import User
    cols = {c.name for c in User.__table__.columns}
    required = {
        "id", "org_id", "email", "name", "role", "status",
        "last_seen_at", "created_at", "updated_at",
    }
    assert required <= cols


def test_audit_log_inherits_tenanted_mixin():
    from app.models import AuditLog
    cols = {c.name for c in AuditLog.__table__.columns}
    required = {
        "id", "org_id", "actor_user_id", "action",
        "target_type", "target_id", "meta", "created_at",
    }
    assert required <= cols
