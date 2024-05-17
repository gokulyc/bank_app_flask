from datetime import datetime, timedelta, UTC
import os

import pathlib
import requests
import pandas as pd

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job
from flask_app_db_factory import db, Transactions, Alerts, get_prod_env_app

app = get_prod_env_app()
db.init_app(app)

BACKEND_FLASK_ROOT_URL = os.getenv("BACKEND_FLASK_ROOT_URL", "http://localhost:5000")


def writeReport():
    dt = datetime.now(UTC)
    # scheduler.print_jobs()
    dt_str = dt.strftime("%Y-%m-%d-%H-%M-%S")
    print(dt)
    # filepath = pathlib.Path(f"./reports/{dt_str}.txt")
    resp = requests.get(
        f"{BACKEND_FLASK_ROOT_URL}/get_report",
        params={"month": dt.month, "year": dt.year},
    )
    if resp.ok:
        data = resp.json()
        print(data)
        df = pd.DataFrame(data)
        report_path = pathlib.Path("reports") / f"{dt_str}.csv"
        df.to_csv(report_path, index=False)
    # filepath.write_text(f"{dt_str}")


def process_low_priority_transactions():
    with app.app_context():
        txns: list[Transactions] = Transactions.query.filter(
            db.and_(
                Transactions.txn_status == "Pending", Transactions.priority == "default"
            )
        ).all()
        pending_txn_count = len(txns)
        if pending_txn_count == 0:
            print("No pending low priority transaction...")
            # print([txn.to_dict() for txn in txns])
        else:
            for txn in txns:
                print(f"updating {txn.id} {txn.priority} {txn.txn_status}")
                txn.txn_status = "Success"
                db.session.add(txn)
                notification = Alerts(
                    message=f"TransactionID: {txn.id} is processed with amount {txn.amount} of current priority({txn.priority}) || {txn.from_account} -> {txn.to_account}"
                )
                db.session.add(notification)
            db.session.commit()
            print("Low priority transactions processed...")


def process_high_priority_transactions():
    with app.app_context():
        txns: list[Transactions] = Transactions.query.filter(
            db.and_(
                Transactions.txn_status == "Pending", Transactions.priority == "high"
            )
        ).all()
        pending_txn_count = len(txns)
        if pending_txn_count == 0:
            print("No pending High priority transaction...")
            # print([txn.to_dict() for txn in txns])
        else:
            for txn in txns:
                print(f"updating {txn.id} {txn.priority} {txn.txn_status}")
                txn.txn_status = "Success"
                db.session.add(txn)
                notification = Alerts(
                    message=f"TransactionID: {txn.id} is processed with amount {txn.amount} of priority({txn.priority}) || {txn.from_account} -> {txn.to_account}"
                )
                db.session.add(notification)
            db.session.commit()
            print("High priority transactions processed...")


def retrieve_jobs_to_schedule():
    jobs: list[Job] = scheduler.get_jobs()
    for j in jobs:
        print(
            f"Name: {j.name} Trigger: {j.trigger} NextRun: {j.next_run_time} Func: {j.func.__name__}"
        )


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    url = "sqlite:///instance/apscheduler.sqlite"
    scheduler.add_jobstore("sqlalchemy", url=url)
    scheduler.add_job(writeReport, "interval", seconds=30)
    # scheduler.add_job(writeReport, "interval", seconds=20)
    scheduler.add_job(process_high_priority_transactions, "interval", seconds=5)
    # scheduler.add_job(
    #     process_pending_transactions, trigger=CronTrigger.from_crontab("0 0 * * *")
    # )
    scheduler.add_job(process_low_priority_transactions, "interval", seconds=60)
    # scheduler.add_job(retrieve_jobs_to_schedule, trigger="interval", seconds=10)

    print("To clear the alarms, delete the apscheduler.sqlite file.")
    print("Press Ctrl+{0} to exit".format("Break" if os.name == "nt" else "C"))
    try:
        scheduler.start()
        print("Scheduler is started...")
        while True:
            pass
    except (KeyboardInterrupt, SystemExit) as e:
        print(e)
        print("Stopping scheduler...")
        scheduler.shutdown()
    # writeReport()
