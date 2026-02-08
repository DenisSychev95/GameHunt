from django.forms.widgets import ClearableFileInput


class SimpleClearableFileInput(ClearableFileInput):
    template_name = "widgets/simple_clearable_file_input.html"


class SimpleClearableFileCheat(ClearableFileInput):
    template_name = "widgets/simple_clearable_file_cheat.html"
