import json
import os
from datetime import datetime, timedelta

# ------------------------ Save input helpers -------------------------------


def safe_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("please enter a valid number.")


def safe_datetime(prompt):
    while True:
        try:
            return datetime.strptime(input(prompt), "%Y-%m-%d %H:%M")
        except ValueError:
            print("invalid date format. use YYYY-MM-DD HH:MM")


def safe_priority(prompt):
    while True:
        p = input(prompt).lower()
        if p in ("low", "medium", "high"):
            return p
        print("priority must be low, medium, or high")

# ------------------------ Task Class -------------------------------


class Task:
    def __init__(self, id, title, description, expiry_date, priority, bullets):
        self.id = id
        self.title = title
        self.description = description
        self.expiry_date = expiry_date
        self.priority = priority
        self.bullets = bullets
        self.status = "not started"

    def is_expired(self):
        return datetime.now() > self.expiry_date

    def is_deletable(self):
        return datetime.now() > self.expiry_date + timedelta(minutes=5)

    def update_status(self):
        is_expired = self.is_expired()
        all_done = all(b["done"] for b in self.bullets)
        any_done = any(["done"] for b in self.bullets)

        match (is_expired, all_done, any_done):
            case (True, _, _):
                self.status = "expired"
            case (False, True, _):
                self.status = "completed"
            case (False, False, True):
                self.status = "in progress..."
            case (False, False, False):
                self.status = "not started"

    def lock_check(self):
        return self.status in ["completed", "expired"]

# ------------------------ Task Manager ----------------------------------


class TaskManager:
    FILE = "tasks.json"

    def __init__(self):
        self.tasks = self.load() or []
        self.remove_duplicates()
        self.save

    def load(self):
        if not os.path.exists(self.FILE):
            return []

        with open(self.FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return []

            data = json.loads(content)
        return self.from_dict(data)

    def save(self):
        with open(self.FILE, "w") as f:
            json.dump(self.to_dict(), f)

    def to_dict(self):
        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "created_date": getattr(t, "created_date", datetime.now()).isoformat(),
                "expiry_date": t.expiry_date.isoformat(),
                "priority": t.priority,
                "status": t.status,
                "bullets": t.bullets,

            }
            for t in self.tasks
        ]

    def from_dict(self, data):
        tasks = []
        for d in data:
            task = []
            for d in data:
                task = Task(
                    d.get("id", 0),
                    d.get("title", "Untitleed"),
                    d.get("description", "no description"),
                    datetime.fromisoformat(
                        d.get("expiry_date", datetime.now().isoformat())),
                    d.get("priority", "low"),
                    d.get("bullets", []),
                )
                task.created_date = datetime.fromisoformat(
                    d.get("created_date", datetime.now().isoformat()))
                task.status = d.get("status", "not started")
                tasks.append(task)
        return tasks

    def remove_duplicates(self):
        unique_tasks = []
        duplicates_count = 0
        seen_tasks = set()
        for t in self.tasks:
            task_hash = (t.title.strip().lower(),
                         t.description.strip().lower(), t.expiry_date)
            if task_hash not in seen_tasks:
                unique_tasks.append(t)
                seen_tasks.add(task_hash)
            else:
                duplicates_count += 1
        if duplicates_count:
            print(f"Remove {duplicates_count} duplicate tasks")
        self.tasks = unique_tasks


# ------------------- Helper ---------------
def get_next_id(manager):
    if not manager.tasks:
        return 1

    return max((task.id for task in manager.tasks), default=0) + 1


# ---------------- Task Function ---------------
def add_task(manager):
    title = input("title: ")
    desc = input("description: ")
    priority = input("priority (Low / Medium / High): ")

    expiry = datetime.strptime(
        input("Expiry (YYYY-MM-DD HH:MM): "), "%Y-%m-%d %H:%M"
    )
    bullets = []
    while True:
        text = input("Bullet (Enter to stop): ")
        if not text:
            break
        bullets.append({"text": text, "done": False})
        task_id = get_next_id(manager)
        task = Task(task_id, title, desc, expiry, priority, bullets)
        manager.tasks.append(task)
        manager.save
        print("Task added.")

# ----------------------- edit task -------------------------------


def edit_task(manager):
    task_id = int(input("Task ID: "))
    found = False

    for task in manager.tasks:
        task.update_status()
        if task.id == task_id:
            found = True
            match task.lock_check():
                case True:
                    print("Task is locked.")
                    return
                case False:
                    task.title = input("New title: ")
                    task.description = input("New description: ")
                    task.expiry_update = datetime.strptime(
                        input("New expiry (YYYY-MM-DD HH:MM): "), "%Y-%m_%d %H:%M"
                    )
                    manager.save()
                    print("Task updated.")
                    return

    match found:
        case False:
            print("Task ID not found.")

# ------------------------ complete bullet task ------------------------------


def complete_bullet(manager):
    # --------------- Get task ID safely --------------------
    while True:
        try:
            task_id = int(input("Task ID: "))
            break
        except ValueError:
            print("please enter a valid ID number.")

# --------------- Find task ---------------------
        task = next((t for t in manager.tasks if t.id == task_id), None)
        match task:
            case None:
                print(f"Task {task_id} not found")
                return
            case _:
                pass

# ------------- Lock check -------------------
        match task.lock_check():
            case True:
                print(f"Task{task_id} is locked.")
                return
            case False:
                pass

# --------------- bullet existence check -------------------
        match bool(task.bullets):
            case False:
                print("this task has no bullets to complete.")
                return
            case True:
                pass

# ----------------- Display bullets using WHILE loop ------------------------
        print("\nBullets")
        i = 0
        while i < len(task.bullets):
            b = task.bullets[i]
            status = "complete" if b["done"] else "not complete"
            print(f"{i + 1}. {b['text']} {status}")
            i += 1

# ------------------- INTERACTIVE bullet selection ------------------------
        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            try:
                index = int(input("bullet number to mark done: ")) - 1
            except ValueError:
                attempts += 1
                print(
                    "invalid number. attempts left: {max_attempt - attempts}")
                continue

            match 0 <= index < len(task.bullets):
                case True:
                    match task.bullets[index]["done"]:
                        case True:
                            print("bullet is alredy marked done")
                        case False:
                            task.bullets[index]["done"] = True
                            task.update_status()
                            manager.save()
                            print("bullet marked as done.")
                    break
                case False:
                    attempts += 1
                    print(
                        f"bullet number out of range. attempts left: {max_attempts - attempts}")

        else:
            print("too many invalid attempts. action cancelled")

# ------------------- view task ----------------------------


def view_tasks(manager):
    match manager.tasks:
        case[]:
            print("No tasks found.")
        case _:
            for task in manager.tasks:
                task.update_status()
                print(f"\nID: {task.id}")
                print(f"Title: {task.title}")
                print(f"Description: {task.description}")
                print(f"Expiry: {task.expiry_date.strftime('%Y-%m-%d %H:%M')}")
                print(f"priority: {task.priority}")
                print(f"status: {task.status}")
                print(f"bullets: {task.bullets}")

                if task.bullets:
                    i = 0
                    while i < len(task.bullets):
                        b = task.bullets[i]
                        status = "complete" if b["done"] else "not complete"
                        print(f"  {i + 1}. {b['text']} {status}")
                        i += 1
                    else:
                        print("No bullets")

# ---------------------- search task --------------------------


def search(manager):
    keyword = input("search: ").lower()
    found = False
    for task in manager.tasks:
        if keyword in task.title.lower() or keyword in task.description.lower():
            print(f"{task.id}: {task.title} ({task.status})")
            found = True
    match found:
        case False:
            print("No matching tasks found.")

# ------------------------- delete task -------------------------


def delete_task(manager):
    match manager.tasks:
        case[]:
            print("No tasks to delete.")
            return
        case _:
            task_id = int(input("Enter the Task ID to date: "))
            i = 0
            found = False
            while i < len(manager.tasks):
                task = manager.tasks[i]
                if task.id == task_id:
                    found = True
                    match task.is_deletable():
                        case True:
                            manager.tasks.pop(i)
                            manager.save()
                            print(f"Task {task_id} deleted.")
                        case False:
                            print(
                                "Task can not be deleted yet (must be expired + 5 min).")
                    break
                i += 1
            match found:
                case False:
                    print(f"Task ID {task_id} not found.")


def cleanup(manager):
    manager.tasks = [t for t in manager.tasks if not t.is_deletable()]
    manager.save()

# ------------------- Menu -----------------------------


def menu():
    print("""
1. Add task
2. Edit task
3. Complete bullet                    
4. Search
5. View task
6. Delete task
7. EXIT
""")

# ----------------Main Loop-------------------


def main():
    manager = TaskManager()

    while True:
        cleanup(manager)
        menu()
        choice = input("Enter your option: ")

        match choice:
            case "1":
                add_task(manager)
            case "2":
                edit_task(manager)
            case "3":
                complete_bullet(manager)
            case "4":
                search(manager)
            case "5":
                view_tasks(manager)
            case "6":
                delete_task(manager)
            case "7":
                break
            case _:
                print("invaild choice. please Enter 1-7.")


main()
print("good bye")
