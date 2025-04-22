import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime
import threading
import time
import pygame

# Initialize pygame mixer for sound playback
pygame.mixer.init()

# Database setup
conn = sqlite3.connect("todo.db")
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        time TEXT,
        completed INTEGER DEFAULT 0,
        priority TEXT DEFAULT 'Medium'
    )
''')
conn.commit()

# Alarm checker
alarms = []

def check_alarms():
    while True:
        now = datetime.now().strftime("%H:%M")
        for alarm_time, title in alarms[:]:
            if now == alarm_time:
                pygame.mixer.music.load("alarm_sound.mp3")
                pygame.mixer.music.play()
                messagebox.showinfo("Alarm", f"Reminder: {title}")
                alarms.remove((alarm_time, title))
        time.sleep(30)

threading.Thread(target=check_alarms, daemon=True).start()

# GUI setup
root = tk.Tk()
root.title("📚 StudyMate - To-Do App")
root.geometry("800x650")
root.resizable(False, False)
root.configure(bg="#F8F8F8")

style = ttk.Style()
style.theme_use("clam")

style.configure("Treeview.Heading", font=("Helvetica", 11, "bold"))
style.configure("Treeview", font=("Helvetica", 10), rowheight=28)
style.map("Treeview", background=[('selected', '#BDE0FE')])

# Task input frame
frame_input = tk.LabelFrame(root, text="Add New Task", font=("Helvetica", 12, "bold"), bg="#EAF4FF", padx=10, pady=10)
frame_input.pack(pady=15, fill="x", padx=20)

title_var = tk.StringVar()
desc_var = tk.StringVar()
time_hour = tk.StringVar(value="HH")
time_minute = tk.StringVar(value="MM")
priority_var = tk.StringVar(value="Medium")

tk.Label(frame_input, text="Title:", bg="#EAF4FF", font=("Helvetica", 10)).grid(row=0, column=0, sticky='w')
tk.Label(frame_input, text="Description:", bg="#EAF4FF", font=("Helvetica", 10)).grid(row=1, column=0, sticky='w')
tk.Label(frame_input, text="Time:", bg="#EAF4FF", font=("Helvetica", 10)).grid(row=2, column=0, sticky='w')
tk.Label(frame_input, text="Priority:", bg="#EAF4FF", font=("Helvetica", 10)).grid(row=2, column=2, sticky='w')

entry_title = tk.Entry(frame_input, textvariable=title_var, width=45, font=("Helvetica", 10))
entry_title.grid(row=0, column=1, padx=5, pady=2, columnspan=3)
entry_desc = tk.Entry(frame_input, textvariable=desc_var, width=45, font=("Helvetica", 10))
entry_desc.grid(row=1, column=1, padx=5, pady=2, columnspan=3)

hour_spinbox = ttk.Spinbox(frame_input, from_=0, to=23, width=5, textvariable=time_hour, format="%02.0f")
minute_spinbox = ttk.Spinbox(frame_input, from_=0, to=59, width=5, textvariable=time_minute, format="%02.0f")
hour_spinbox.grid(row=2, column=1, padx=(5,0), pady=2, sticky='w')
minute_spinbox.grid(row=2, column=1, padx=(60,0), pady=2, sticky='w')

priority_menu = ttk.Combobox(frame_input, textvariable=priority_var, values=["High", "Medium", "Low"], width=17)
priority_menu.grid(row=2, column=3, padx=5, pady=2)

def add_task():
    title = title_var.get()
    desc = desc_var.get()
    t = f"{int(time_hour.get()):02}:{int(time_minute.get()):02}" if time_hour.get().isdigit() and time_minute.get().isdigit() else ""
    priority = priority_var.get()

    if not title:
        messagebox.showwarning("Input Error", "Title is required")
        return

    c.execute("INSERT INTO tasks (title, description, time, priority) VALUES (?, ?, ?, ?)", (title, desc, t, priority))
    conn.commit()
    if t:
        alarms.append((t, title))
    refresh_tasks()
    title_var.set("")
    desc_var.set("")
    time_hour.set("HH")
    time_minute.set("MM")
    priority_var.set("Medium")

btn_add = tk.Button(frame_input, text="Add Task", command=add_task, bg="#3B82F6", fg="white", font=("Helvetica", 10, "bold"))
btn_add.grid(row=3, column=1, pady=10)

# Task list frame
frame_tasks = tk.LabelFrame(root, text="Your Tasks", font=("Helvetica", 12, "bold"), bg="#F0F8FF", padx=10, pady=10)
frame_tasks.pack(padx=20, pady=10, fill="both", expand=True)

columns = ("Title", "Description", "Time", "Priority", "Completed")
tree = ttk.Treeview(frame_tasks, columns=columns, show='headings', height=12)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor='center')
tree.pack(fill="both", expand=True)

scroll_y = ttk.Scrollbar(frame_tasks, orient="vertical", command=tree.yview)
scroll_y.pack(side="right", fill="y")
tree.configure(yscrollcommand=scroll_y.set)

def refresh_tasks():
    for row in tree.get_children():
        tree.delete(row)
    c.execute("SELECT id, title, description, time, priority, completed FROM tasks")
    for task in c.fetchall():
        display_task = list(task)
        display_task[5] = "Yes" if task[5] == 1 else "No"
        tag = display_task[4].lower()
        tree.insert('', tk.END, values=display_task[1:], tags=(tag,))
    tree.tag_configure("high", background="#FFE5E5")
    tree.tag_configure("medium", background="#FFFBD6")
    tree.tag_configure("low", background="#E5FFE5")

refresh_tasks()

def delete_task():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Select Task", "No task selected")
        return
    title = tree.item(selected)['values'][0]
    c.execute("DELETE FROM tasks WHERE title=?", (title,))
    conn.commit()
    refresh_tasks()

def mark_completed():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Select Task", "No task selected")
        return
    title = tree.item(selected)['values'][0]
    c.execute("UPDATE tasks SET completed=1 WHERE title=?", (title,))
    conn.commit()
    refresh_tasks()

def filter_completed():
    for row in tree.get_children():
        tree.delete(row)
    c.execute("SELECT id, title, description, time, priority, completed FROM tasks WHERE completed=1")
    for task in c.fetchall():
        display_task = list(task)
        display_task[5] = "Yes"
        tag = display_task[4].lower()
        tree.insert('', tk.END, values=display_task[1:], tags=(tag,))

def clear_filter():
    refresh_tasks()

def sort_by_priority():
    for row in tree.get_children():
        tree.delete(row)
    c.execute("SELECT id, title, description, time, priority, completed FROM tasks ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END")
    for task in c.fetchall():
        display_task = list(task)
        display_task[5] = "Yes" if task[5] == 1 else "No"
        tag = display_task[4].lower()
        tree.insert('', tk.END, values=display_task[1:], tags=(tag,))

def sort_by_time():
    for row in tree.get_children():
        tree.delete(row)
    c.execute("SELECT id, title, description, time, priority, completed FROM tasks ORDER BY time")
    for task in c.fetchall():
        display_task = list(task)
        display_task[5] = "Yes" if task[5] == 1 else "No"
        tag = display_task[4].lower()
        tree.insert('', tk.END, values=display_task[1:], tags=(tag,))

# Frame for action buttons
frame_buttons = tk.Frame(root, bg="#F8F8F8")
frame_buttons.pack(pady=10)

btn_delete = tk.Button(frame_buttons, text="🗑️ Delete Task", command=delete_task, bg="#EF4444", fg="white", width=20)
btn_complete = tk.Button(frame_buttons, text="✅ Mark Completed", command=mark_completed, bg="#10B981", fg="white", width=20)
btn_filter = tk.Button(frame_buttons, text="✔ Show Completed", command=filter_completed, bg="#F59E0B", fg="white", width=20)
btn_clear = tk.Button(frame_buttons, text="🔄 Show All", command=clear_filter, bg="#6366F1", fg="white", width=20)
btn_sort_priority = tk.Button(frame_buttons, text="⬆️ Sort by Priority", command=sort_by_priority, bg="#3B82F6", fg="white", width=20)
btn_sort_time = tk.Button(frame_buttons, text="🕒 Sort by Time", command=sort_by_time, bg="#0EA5E9", fg="white", width=20)

btn_delete.grid(row=0, column=0, padx=6, pady=6)
btn_complete.grid(row=0, column=1, padx=6, pady=6)
btn_filter.grid(row=1, column=0, padx=6, pady=6)
btn_clear.grid(row=1, column=1, padx=6, pady=6)
btn_sort_priority.grid(row=2, column=0, padx=6, pady=6)
btn_sort_time.grid(row=2, column=1, padx=6, pady=6)

root.mainloop()
conn.close() 