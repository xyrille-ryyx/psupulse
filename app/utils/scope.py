"""Role-based data scope: which units a staff member may see."""
from app.models import Unit

OVERALL = "all"


def can_see_overall(user):
    return user.role in ("admin", "student_affairs")


def visible_unit_ids(user):
    """None means unrestricted. Faculty see their courses; heads see their department tree."""
    if can_see_overall(user):
        return None
    if user.role in ("faculty", "dept_head"):
        ids = set()
        for unit in user.units:
            ids.update(unit.descendant_ids())
        return ids
    return set()


def visible_units(user):
    """Visible units in tree order (college, its departments, their courses, ...)."""
    ids = visible_unit_ids(user)
    ordered = []

    def walk(unit):
        if ids is None or unit.id in ids:
            ordered.append(unit)
        for child in unit.children:
            walk(child)

    for root in Unit.query.filter(Unit.parent_id.is_(None)).order_by(Unit.code).all():
        walk(root)
    return ordered


def can_see_unit(user, unit_id):
    """unit_id None = university-wide view."""
    if unit_id is None:
        return can_see_overall(user)
    ids = visible_unit_ids(user)
    return ids is None or unit_id in ids
