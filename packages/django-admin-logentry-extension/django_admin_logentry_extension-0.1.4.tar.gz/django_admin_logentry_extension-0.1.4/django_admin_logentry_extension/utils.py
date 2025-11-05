from django.contrib.admin.models import LogEntry


def add_extra_action_flags(extra_action_flags):
    action_flag_field = LogEntry._meta.get_field("action_flag")
    for item in extra_action_flags:
        if isinstance(action_flag_field.choices, tuple):
            action_flag_field.choices = list(action_flag_field.choices)
        action_flag_field.choices.append(item)
