import time

from dflow import InputParameter, Inputs, Step, Steps, Workflow, config
from dflow.python import OP, OPIO, OPIOSign, PythonOPTemplate, upload_packages

config["mode"] = "debug"

if "__file__" in locals():
    upload_packages.append(__file__)


class Plus1(OP):
    def __init__(self):
        pass

    @classmethod
    def get_input_sign(cls):
        return OPIOSign({
            'iter': int
        })

    @classmethod
    def get_output_sign(cls):
        return OPIOSign({
            'iter': int
        })

    @OP.exec_sign_check
    def execute(
            self,
            op_in: OPIO,
    ) -> OPIO:
        print("This is iter %i" % op_in["iter"])
        return OPIO({
            'iter': op_in['iter'] + 1
        })


def test_recurse():
    steps = Steps(name="iter", inputs=Inputs(
        parameters={"iter": InputParameter(value=0),
                    "limit": InputParameter(value=5)}))
    plus1 = Step(name="plus1",
                 template=PythonOPTemplate(Plus1,
                                           image="python:3.8"),
                 parameters={"iter": steps.inputs.parameters["iter"]},
                 key="iter-%s" % steps.inputs.parameters["iter"])
    steps.add(plus1)
    next = Step(name="next", template=steps,
                parameters={"iter": plus1.outputs.parameters["iter"]},
                when="%s < %s" % (
                    plus1.outputs.parameters["iter"],
                    steps.inputs.parameters["limit"]))
    steps.add(next)

    wf = Workflow("recurse", steps=steps)
    wf.submit()

    while wf.query_status() in ["Pending", "Running"]:
        time.sleep(1)

    assert(wf.query_status() == "Succeeded")
    step = wf.query_step(key="iter-4")[0]
    assert(step.phase == "Succeeded")
    assert step.outputs.parameters["iter"].value == 5


if __name__ == "__main__":
    test_recurse()
