"""Pure three-way merge of canonical project source."""
from copy import deepcopy

from app.errors import AdawError


_MISSING = object()
_ENTITY_LISTS = {"tracks", "buses", "events", "sections"}
_PROCESSOR_IDENTITY = ("registry_id", "catalog_sha256", "state_sha256", "module_sha256", "key_bus")
_TIMING_FIELDS = ("schema", "tempo", "ppq", "sample_rate", "length_ticks", "time_map")


def _processor_identity(processor):
    return tuple(processor.get(key) for key in _PROCESSOR_IDENTITY)


def _timing_content(source):
    return source["sections"], [(track["id"], track["events"]) for track in source["tracks"]]


def merge_source(base, current, proposed, *, base_revision, current_revision):
    """Merge disjoint edits by stable entity ID and report conflicts without writes.

    Ordered insert topology and simultaneous edits to entity membership/order
    require an explicit resolution. Parameter fields merge within an unchanged
    processor identity, including its catalog and opaque state hashes.
    """
    conflicts = []

    def conflict(path, reason, old, head, candidate):
        entry = {"path": list(path), "reason": reason}
        for key, value in (("base", old), ("current", head), ("proposed", candidate)):
            entry[key] = None if value is _MISSING else value
        if any(value is _MISSING for value in (old, head, candidate)):
            entry["missing"] = [key for key, value in
                                (("base", old), ("current", head), ("proposed", candidate))
                                if value is _MISSING]
        conflicts.append(entry)
        return head

    def merge(path, old, head, candidate):
        if old == candidate or head == candidate:
            return head
        if old == head:
            return candidate
        if all(isinstance(value, dict) for value in (old, head, candidate)):
            if any(key in old for key in _PROCESSOR_IDENTITY) and (
                _processor_identity(old) != _processor_identity(head)
                or _processor_identity(old) != _processor_identity(candidate)
            ):
                return conflict(path, "PROCESSOR_BINDING_CHANGED", old, head, candidate)
            if head.get("protected") is True and "events" in old and (
                old["events"] != candidate.get("events") and head.get("events") != candidate.get("events")
            ):
                return conflict(path + ("events",), "PROTECTED_EVENTS", old["events"],
                                head.get("events"), candidate.get("events"))
            result = {}
            for key in sorted(old.keys() | head.keys() | candidate.keys()):
                value = merge(path + (key,), old.get(key, _MISSING),
                              head.get(key, _MISSING), candidate.get(key, _MISSING))
                if value is not _MISSING:
                    result[key] = value
            return result
        if all(isinstance(value, list) for value in (old, head, candidate)):
            if path[-1] in _ENTITY_LISTS:
                ids = [[item["id"] for item in items] for items in (old, head, candidate)]
                order = merge(path + ("order",), *ids)
                maps = [{item["id"]: item for item in items} for items in (old, head, candidate)]
                merged = {}
                for item_id in dict.fromkeys([*ids[0], *ids[1], *ids[2]]):
                    item = merge(path + (item_id,), *(items.get(item_id, _MISSING) for items in maps))
                    if item is not _MISSING:
                        merged[item_id] = item
                return [merged[item_id] for item_id in order if item_id in merged]
            if path[-1] == "inserts":
                # These arrays are the established source order. Slot-level merges
                # are valid only while every processor identity stays in place.
                signatures = [[_processor_identity(item) for item in items]
                              for items in (old, head, candidate)]
                if signatures[0] == signatures[1] == signatures[2]:
                    return [merge(path + (index,), *values)
                            for index, values in enumerate(zip(old, head, candidate, strict=True))]
                return conflict(path, "PROCESSOR_CHAIN_CHANGED", old, head, candidate)
        if old is _MISSING:
            reason = "DIVERGENT_ADDITION"
        elif head is _MISSING or candidate is _MISSING:
            reason = "TARGET_REMOVED"
        else:
            reason = "DIVERGENT_EDIT"
        return conflict(path, reason, old, head, candidate)

    if current != base and current != proposed:
        head_changed_timing = any(base.get(key) != current.get(key) for key in _TIMING_FIELDS)
        candidate_changed_timing = any(base.get(key) != proposed.get(key) for key in _TIMING_FIELDS)
        head_changed_events = _timing_content(base) != _timing_content(current)
        candidate_changed_events = _timing_content(base) != _timing_content(proposed)
        for key in _TIMING_FIELDS:
            values = (base.get(key, _MISSING), current.get(key, _MISSING), proposed.get(key, _MISSING))
            old, head, candidate = values
            if ((old != head and candidate_changed_events)
                or (old != candidate and head_changed_events)
                or (head != candidate and head_changed_timing and candidate_changed_timing)):
                conflict((key,), "TIMING_CONTEXT_CHANGED", *values)
    result = merge((), base, current, proposed)
    if conflicts:
        raise AdawError("CONFLICT", "Resolve conflicting source edits against the current revision",
                        base_revision=base_revision, current_revision=current_revision, conflicts=conflicts)
    return deepcopy(result)
