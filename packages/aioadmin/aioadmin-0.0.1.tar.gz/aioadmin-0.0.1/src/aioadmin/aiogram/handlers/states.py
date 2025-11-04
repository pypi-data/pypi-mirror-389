from aiogram.fsm.state import State, StatesGroup

class Menu(StatesGroup):
    get_tables = State()
    get_table = State()
    delete_records = State()
    create_record = State()
    select_record_to_update = State()
    select_column_to_update = State()
    update_field_value = State()


