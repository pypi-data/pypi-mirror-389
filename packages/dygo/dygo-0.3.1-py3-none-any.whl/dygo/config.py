DYGO_PROGRAM_NAME = "Dynamic Gooeyz"
DYGO_PROGRAM_DESCRIPTION = "Select parameters dynamically from a config file"


def set_program_metadata(program_name: str, program_description: str):
    global DYGO_PROGRAM_NAME, DYGO_PROGRAM_DESCRIPTION  # noqa PLW0603

    DYGO_PROGRAM_NAME = program_name
    DYGO_PROGRAM_DESCRIPTION = program_description


def get_program_name() -> str:
    return DYGO_PROGRAM_NAME


def get_program_description() -> str:
    return DYGO_PROGRAM_DESCRIPTION
