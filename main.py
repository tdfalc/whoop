from datetime import datetime as dt
import os
from pathlib import Path

import pytz

from whoop.client import RecoveryClient
from whoop.plot import plot_recovery

if __name__ == "__main__":
    savedir = Path(__file__).parent / "docs"
    os.makedirs(savedir, exist_ok=True)

    username = os.getenv("WHOOP_USERNAME")
    password = os.getenv("WHOOP_PASSWORD")

    start_date = dt(2024, 2, 1, tzinfo=pytz.utc)
    end_date = dt(2024, 4, 20, tzinfo=pytz.utc)
    client = RecoveryClient(username, password)
    recovery = client.get_recovery(start_date, end_date)
    plot_recovery(recovery, savedir)
