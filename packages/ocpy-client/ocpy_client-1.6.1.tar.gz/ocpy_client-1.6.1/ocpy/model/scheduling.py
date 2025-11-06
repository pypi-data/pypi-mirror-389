#  Copyright (c) 2019. Tobias Kurze

import json
from datetime import datetime
from typing import List, Optional

import pendulum


class Scheduling:
    def __init__(
        self,
        agent_id: str,
        start: str | pendulum.DateTime,
        end: str | pendulum.DateTime,
        inputs: Optional[List[str]] = None,
    ):
        self.agent_id = agent_id
        if isinstance(start, str):
            parsed = pendulum.parse(start)
            if (
                isinstance(parsed, pendulum.Duration)
                or isinstance(parsed, pendulum.Time)
                or isinstance(parsed, pendulum.Date)
            ):
                raise ValueError(
                    "Start time cannot be a duration, time, or date, must be a datetime"
                )
            start = parsed
        self.start = start
        if isinstance(end, str):
            parsed = pendulum.parse(end)
            if (
                isinstance(parsed, pendulum.Duration)
                or isinstance(parsed, pendulum.Time)
                or isinstance(parsed, pendulum.Date)
            ):
                raise ValueError(
                    "End time cannot be a duration, time, or date, must be a datetime"
                )
            end = parsed

        if isinstance(end, pendulum.Duration):
            raise ValueError("End time cannot be a duration")

        self.end = end
        self.inputs = ["defaults"] if inputs is None else inputs

    def __str__(self):
        return json.dumps(self.get_scheduling_dict())

    def __repr__(self):
        return self.__str__()

    def get_scheduling_dict(self):
        return {
            "agent_id": self.agent_id,
            "inputs": self.inputs,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }

    def get_agent_id(self) -> str:
        return self.agent_id

    def get_inputs(self) -> List[str]:
        return self.inputs

    def get_start(self) -> datetime:
        return self.start

    def get_end(self) -> datetime:
        return self.end


if __name__ == "__main__":
    dt = pendulum.parse("2022-06-22T11:55:00Z")
    print(dt)
    print(type(dt))
    assert isinstance(dt, pendulum.DateTime)
    print(dt.timezone)
    print(dt.isoformat())

    s = Scheduling(
        agent_id="test SMP", start="2022-06-22T11:55:00Z", end="2022-06-22T12:59:00Z"
    )
    print(s)
