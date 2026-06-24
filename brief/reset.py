from .state import WeekState

if __name__ == "__main__":
    state = WeekState.load()
    state.weekly_reset()      # base programme; keeps persist:true constraints
    state.save()