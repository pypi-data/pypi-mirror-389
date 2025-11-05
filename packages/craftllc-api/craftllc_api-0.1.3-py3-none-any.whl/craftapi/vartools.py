class VarTools:
    def __init__(self, varlist):
        self.varlist = varlist
    
    def get_var_value(self, var):
        return self.varlist[var]
    
    def clean_type(self, var):
        var_type = str(type(self.varlist[var]))
        result = var_type.split("'")[1]
        return result

    def format_time(self, seconds):
        endings = {
            "секунда": ["секунда", "секунди", "секунд"],
            "хвилина": ["хвилина", "хвилини", "хвилин"],
            "година": ["година", "години", "годин"],
            "день": ["день", "дня", "днів"],
            "тиждень": ["тиждень", "тижня", "тижнів"],
            "місяць": ["місяць", "місяця", "місяців"],
            "рік": ["рік", "роки", "років"]
        }

        units = [
            ("рік", 365 * 24 * 60 * 60),
            ("місяць", 30 * 24 * 60 * 60),
            ("тиждень", 7 * 24 * 60 * 60),
            ("день", 24 * 60 * 60),
            ("година", 60 * 60),
            ("хвилина", 60),
            ("секунда", 1)
        ]

        for unit, duration in units:
            if seconds >= duration:
                number = seconds // duration
                if 11 <= number % 100 <= 19:
                    form = endings[unit][2]
                else:
                    last_digit = number % 10
                    if last_digit == 1:
                        form = endings[unit][0]
                    elif 2 <= last_digit <= 4:
                        form = endings[unit][1]
                    else:
                        form = endings[unit][2]
                return f"{number} {form}"
