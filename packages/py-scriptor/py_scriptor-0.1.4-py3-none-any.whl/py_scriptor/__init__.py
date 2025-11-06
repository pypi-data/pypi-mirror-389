import traceback

class RuleScript:
    def __init__(self, script, vars = {}):
        scriptS = "".join(script.splitlines())
        if len(script.split("::")) == 1:
            self.rules = self.parse(script)
            self.imports = []
        else:
            self.rules = self.parse(script.split("::")[-1])
            self.imports = script.split("::")[0:-1]
        self.vars = vars
    def setVar(self, var, wal):
        self.vars[var] = wal
    def getVar(self, var):
        return self.vars[var]
    @staticmethod
    def parse(script):
        rules = []
        for line in script.split(";"):
            if ">>>" in line:
                cond, actions = line.split(">>>")
                rules.append((cond.strip(), actions.strip()))
        return rules

    def run(self, max_steps=1000):
        for impo in self.imports:
            try:
                self.vars[impo] = __import__(impo)
            except ImportError as e:
                print(f"Import error: {e}")
                return False

        steps = 0
        self.vars["start"] = True
        while steps < max_steps:
            for cond, actions in self.rules:
                if self.eval_expr(cond):
                    for action in actions.split(","):
                        if not self.execute(action.strip()):
                            return False
            self.vars["start"] = False
            steps += 1
        return True

    def getImports(self):
        return "\n".join(f"import {impo}" for impo in self.imports)

    def eval_expr(self, expr):
        try:
            return eval(expr, {}, self.vars)
        except Exception as e:
            print(f"Execution error: {e}")
            traceback.print_exc()
            return False

    def execute(self, action):
        try:
               exec(action, {}, self.vars)
               return True
        except Exception as e:

            print(f"Execution error: {e}")
            traceback.print_exc()
            return False



