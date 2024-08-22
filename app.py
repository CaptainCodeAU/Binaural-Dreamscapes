import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sounddevice as sd
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import sqlite3
import os

"""
Binaural Dreamscapes v1.0

This application generates binaural audio and provides a graphical user interface
for controlling and visualizing the audio output. It allows users to adjust
frequencies, phases, and volume for left and right audio channels independently.

The app also includes functionality to save and load configurations, and
provides visual representation of the generated waveforms.

Author: Captain Code
Date: 2024
"""

# Global variables
window_width = 800
window_height = 900

volume = 0.2  # Volume between 0.0 and 1.0
frequency_left = 100  # Hz
frequency_right = 104  # Hz
sampling_rate = 44100  # Hz
stream = None
phase_left = 0  # degrees
phase_right = 0  # degrees
volume_value_label = None  # Initialize volume_value_label as None

# SQLite setup
db_file = "dreamscapes.db"
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS configurations (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        frequency_left REAL,
        frequency_right REAL,
        phase_left REAL,
        phase_right REAL,
        volume REAL
    )
"""
)
conn.commit()


def plot_waveforms():
    """
    Plot the waveforms for both left and right channels based on current settings.
    This function updates the matplotlib figure with the current waveform data.
    """
    global frequency_left, frequency_right, phase_left, phase_right, canvas, ax1, ax2

    duration = 0.05  # duration in seconds for the plot (e.g. 50ms)
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    radian_phase_left = phase_left * np.pi / 180
    radian_phase_right = phase_right * np.pi / 180
    wave1 = 0.5 * np.sin(2 * np.pi * frequency_left * t + radian_phase_left)
    wave2 = 0.5 * np.sin(2 * np.pi * frequency_right * t + radian_phase_right)

    # Clear existing content on axes
    ax1.clear()
    ax2.clear()

    # Plotting on the existing axes
    ax1.plot(t, wave1, color="#669bbc", linewidth=2)
    ax1.set_title(
        f"Left Waveform: {frequency_left:.1f} Hz, Phase: {phase_left:.1f}°",
        fontsize=10,
        color="#333333",
    )
    ax1.set_xlabel("Time (s)", fontsize=8, color="#666666")
    ax1.set_ylabel("Amplitude", fontsize=8, color="#666666")
    ax1.grid(True, linestyle="--", alpha=0.7)
    ax1.set_ylim(-0.6, 0.6)
    ax1.tick_params(axis="both", which="major", labelsize=7, colors="#666666")

    ax2.plot(t, wave2, color="#81b29a", linewidth=2)
    ax2.set_title(
        f"Right Waveform: {frequency_right:.1f} Hz, Phase: {phase_right:.1f}°",
        fontsize=10,
        color="#333333",
    )
    ax2.set_xlabel("Time (s)", fontsize=8, color="#666666")
    ax2.set_ylabel("Amplitude", fontsize=8, color="#666666")
    ax2.grid(True, linestyle="--", alpha=0.7)
    ax2.set_ylim(-0.6, 0.6)
    ax2.tick_params(axis="both", which="major", labelsize=7, colors="#666666")

    # Adjust the spacing between the plots
    fig.subplots_adjust(hspace=0.4)

    # Set background color
    fig.patch.set_facecolor("#f0f0f0")
    ax1.set_facecolor("#ffffff")
    ax2.set_facecolor("#ffffff")

    # Drawing the updated plot
    canvas.draw()


def update_frequency_left_slider(val):
    """Update the left frequency entry field when the slider is moved."""
    frequency_left_entry.delete(0, tk.END)
    frequency_left_entry.insert(0, f"{float(val):.1f}")
    update_frequency_left(from_slider=True)


def update_frequency_right_slider(val):
    """Update the right frequency entry field when the slider is moved."""
    frequency_right_entry.delete(0, tk.END)
    frequency_right_entry.insert(0, f"{float(val):.1f}")
    update_frequency_right(from_slider=True)


def update_phase_left_slider(val):
    """Update the left phase entry field when the slider is moved."""
    phase_left_entry.delete(0, tk.END)
    phase_left_entry.insert(0, f"{float(val):.1f}")
    update_phase_left(from_slider=True)


def update_phase_right_slider(val):
    """Update the right phase entry field when the slider is moved."""
    phase_right_entry.delete(0, tk.END)
    phase_right_entry.insert(0, f"{float(val):.1f}")
    update_phase_right(from_slider=True)


def audio_callback(outdata, frames, time, status):
    """
    Callback function for generating audio data.
    This function is called by the sound device stream to fill the output buffer.
    """
    global frequency_left, frequency_right, phase_left, phase_right, volume
    t = (np.arange(frames) + time.outputBufferDacTime * sampling_rate) % sampling_rate
    radian_phase_left = phase_left * np.pi / 180
    radian_phase_right = phase_right * np.pi / 180
    outdata[:, 0] = (
        volume
        * 0.5
        * np.sin(2 * np.pi * frequency_left * t / sampling_rate + radian_phase_left)
    )  # Left channel
    outdata[:, 1] = (
        volume
        * 0.5
        * np.sin(2 * np.pi * frequency_right * t / sampling_rate + radian_phase_right)
    )  # Right channel


def update_frequency_left(from_slider=False, event=None):
    """
    Update the left channel frequency.
    This function is called when the user changes the frequency via entry field or slider.
    """
    global frequency_left
    try:
        new_frequency = float(frequency_left_entry.get())
        if 1 <= new_frequency <= 20000:
            frequency_left = new_frequency
            if not from_slider:
                frequency_left_slider.set(frequency_left)
            plot_waveforms()  # Automatically update the plot
        else:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Invalid Value",
            "Please enter a valid number between 1 and 20000 for Frequency Left.",
        )
        frequency_left_entry.delete(0, tk.END)
        frequency_left_entry.insert(0, f"{frequency_left:.1f}")
        frequency_left_slider.set(frequency_left)


def update_frequency_right(from_slider=False, event=None):
    """
    Update the right channel frequency.
    This function is called when the user changes the frequency via entry field or slider.
    """
    global frequency_right
    try:
        new_frequency = float(frequency_right_entry.get())
        if 1 <= new_frequency <= 20000:
            frequency_right = new_frequency
            if not from_slider:
                frequency_right_slider.set(frequency_right)
            plot_waveforms()  # Automatically update the plot
        else:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Invalid Value",
            "Please enter a valid number between 1 and 20000 for Frequency Right.",
        )
        frequency_right_entry.delete(0, tk.END)
        frequency_right_entry.insert(0, f"{frequency_right:.1f}")
        frequency_right_slider.set(frequency_right)


def update_phase_left(from_slider=False, event=None):
    """
    Update the left channel phase.
    This function is called when the user changes the phase via entry field or slider.
    """
    global phase_left
    try:
        new_phase = float(phase_left_entry.get())
        if 0 <= new_phase <= 360:
            phase_left = new_phase
            if not from_slider:
                phase_left_slider.set(phase_left)
            plot_waveforms()  # Automatically update the plot
        else:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Invalid Value",
            "Please enter a valid number between 0 and 360 for Phase Left.",
        )
        phase_left_entry.delete(0, tk.END)
        phase_left_entry.insert(0, f"{phase_left:.1f}")
        phase_left_slider.set(phase_left)


def update_phase_right(from_slider=False, event=None):
    """
    Update the right channel phase.
    This function is called when the user changes the phase via entry field or slider.
    """
    global phase_right
    try:
        new_phase = float(phase_right_entry.get())
        if 0 <= new_phase <= 360:
            phase_right = new_phase
            if not from_slider:
                phase_right_slider.set(phase_right)
            plot_waveforms()  # Automatically update the plot
        else:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Invalid Value",
            "Please enter a valid number between 0 and 360 for Phase Right.",
        )
        phase_right_entry.delete(0, tk.END)
        phase_right_entry.insert(0, f"{phase_right:.1f}")
        phase_right_slider.set(phase_right)


def update_volume(val):
    """
    Update the volume based on the slider value.
    This function is called when the user moves the volume slider.
    """
    global volume, volume_value_label
    volume = float(val) / 100  # Convert percentage to a 0.0 to 1.0 range
    if volume_value_label:
        volume_value_label.config(
            text=f"{int(float(val))}%"
        )  # Update volume value label


def start_stream():
    """Start the audio stream."""
    global stream
    buffer_size = 1024 * 2  # Adjust this value as needed
    if stream is None or not stream.active:
        stream = sd.OutputStream(
            samplerate=sampling_rate,
            channels=2,
            callback=audio_callback,
            blocksize=buffer_size,
        )
        stream.start()
        start_button.config(state="disabled")
        stop_button.config(state="normal")


def stop_stream():
    """Stop the audio stream."""
    global stream
    if stream is not None and stream.active:
        stream.stop()
        start_button.config(state="normal")
        stop_button.config(state="disabled")


def show_about_dialog():
    """Display the About dialog."""
    about_dialog = tk.Toplevel(root)
    about_dialog.title("About")
    about_dialog.geometry("300x150")
    about_dialog.resizable(False, False)

    # Center the dialog
    center_dialog(about_dialog)

    about_label = tk.Label(
        about_dialog,
        text="Binaural Dreamscapes\nVersion 1.0\n(c) 2024 Captain Code",
        font=("Helvetica", 12),
    )
    about_label.pack(expand=True)

    # Add a close button
    close_button = ttk.Button(about_dialog, text="Close", command=about_dialog.destroy)
    close_button.pack(pady=10)


def show_help_dialog():
    """Display the Help dialog."""
    help_dialog = tk.Toplevel(root)
    help_dialog.title("Help")
    help_dialog.geometry("400x200")
    help_dialog.resizable(False, False)

    # Center the dialog
    center_dialog(help_dialog)

    help_text = """
    This app generates binaural audio:

    1. Set left and right frequencies
    2. Adjust phases if desired
    3. Set volume
    4. Click 'Start' to begin playback
    5. Click 'Stop' to end playback

    Save and load configurations using the File menu.
    """

    help_label = tk.Label(
        help_dialog, text=help_text, font=("Helvetica", 10), justify="left"
    )
    help_label.pack(expand=True, padx=20, pady=20)

    # Add a close button
    close_button = ttk.Button(help_dialog, text="Close", command=help_dialog.destroy)
    close_button.pack(pady=10)


def center_dialog(dialog):
    """Center a dialog window relative to the main window."""
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = root.winfo_x() + (root.winfo_width() // 2) - (width // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (height // 2)
    dialog.geometry(f"+{x}+{y}")


def save_configuration():
    """
    Save the current configuration to the database.
    This function opens a dialog for the user to enter a name for the configuration.
    """
    global frequency_left, frequency_right, phase_left, phase_right, volume

    # Create a custom dialog
    save_dialog = tk.Toplevel(root)
    save_dialog.title("Save Configuration")
    save_dialog.geometry("300x150")
    save_dialog.resizable(False, False)

    # Center the dialog
    center_dialog(save_dialog)

    tk.Label(
        save_dialog, text="Enter a name for this configuration:", font=("Helvetica", 10)
    ).pack(pady=(20, 5))
    name_entry = ttk.Entry(save_dialog, width=30)
    name_entry.pack(pady=5)

    def save():
        """Inner function to handle the saving process."""
        name = name_entry.get()
        if name:
            try:
                cursor.execute(
                    """
                    INSERT INTO configurations (name, frequency_left, frequency_right, phase_left, phase_right, volume)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        name,
                        frequency_left,
                        frequency_right,
                        phase_left,
                        phase_right,
                        volume,
                    ),
                )
                conn.commit()
                messagebox.showinfo(
                    "Success", f"Configuration '{name}' saved successfully."
                )
                save_dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror(
                    "Error", f"A configuration with the name '{name}' already exists."
                )
        else:
            messagebox.showerror("Error", "Please enter a name for the configuration.")

    save_button = ttk.Button(save_dialog, text="Save", command=save, width=10)
    save_button.pack(pady=(10, 0))


def load_configuration():
    """
    Load a saved configuration from the database.
    This function opens a dialog for the user to select a configuration to load.
    """
    global frequency_left, frequency_right, phase_left, phase_right, volume
    cursor.execute("SELECT name FROM configurations")
    configurations = cursor.fetchall()
    if not configurations:
        messagebox.showinfo("No Configurations", "There are no saved configurations.")
        return

    config_names = [config[0] for config in configurations]

    # Create a new dialog window
    dialog = tk.Toplevel(root)
    dialog.title("Load Configuration")
    dialog.geometry("300x300")
    dialog.resizable(False, False)

    # Center the dialog
    center_dialog(dialog)

    # Create a frame to hold the listbox and scrollbar
    frame = ttk.Frame(dialog)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Create a scrollbar
    scrollbar = ttk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create a listbox to display configuration names
    listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Helvetica", 10))
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Configure the scrollbar
    scrollbar.config(command=listbox.yview)

    # Populate the listbox with configuration names
    for name in config_names:
        listbox.insert(tk.END, name)

    def load_selected_config():
        """Inner function to handle the loading process."""
        selection = listbox.curselection()
        if selection:
            name = listbox.get(selection[0])
            cursor.execute("SELECT * FROM configurations WHERE name = ?", (name,))
            config = cursor.fetchone()
            if config:
                global frequency_left, frequency_right, phase_left, phase_right, volume
                (
                    _,
                    _,
                    frequency_left,
                    frequency_right,
                    phase_left,
                    phase_right,
                    volume,
                ) = config
                update_ui_values()
                dialog.destroy()
        else:
            messagebox.showerror("Error", "Please select a configuration to load.")

    # Add a Load button
    load_button = ttk.Button(dialog, text="Load", command=load_selected_config, width=10)
    load_button.pack(pady=10)

    # Bind double-click event to the listbox
    listbox.bind('<Double-1>', lambda event: load_selected_config())


def update_ui_values():
    """Update all UI elements with the current global values."""
    global volume_value_label
    frequency_left_entry.delete(0, tk.END)
    frequency_left_entry.insert(0, f"{frequency_left:.1f}")
    frequency_left_slider.set(frequency_left)

    frequency_right_entry.delete(0, tk.END)
    frequency_right_entry.insert(0, f"{frequency_right:.1f}")
    frequency_right_slider.set(frequency_right)

    phase_left_entry.delete(0, tk.END)
    phase_left_entry.insert(0, f"{phase_left:.1f}")
    phase_left_slider.set(phase_left)

    phase_right_entry.delete(0, tk.END)
    phase_right_entry.insert(0, f"{phase_right:.1f}")
    phase_right_slider.set(phase_right)

    volume_slider.set(volume * 100)
    if volume_value_label:
        volume_value_label.config(
            text=f"{int(volume * 100)}%"
        )  # Update volume value label
    plot_waveforms()  # Update the plot after loading a configuration


# GUI Setup
root = tk.Tk()
root.title("Binaural Dreamscapes v1.0")
root.resizable(False, False)
root.configure(bg="#f0f0f0")

# Apply a modern style
style = ttk.Style()
style.theme_use("clam")

# Create a main frame to hold all widgets
main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

# Figure plotting
fig = Figure(figsize=(10, 4), dpi=100)
ax1 = fig.add_subplot(211)
ax2 = fig.add_subplot(212)
canvas = FigureCanvasTkAgg(fig, master=main_frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 20))

# Create frames for organizing widgets
controls_frame = ttk.Frame(main_frame)
controls_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

left_frame = ttk.Frame(controls_frame)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

right_frame = ttk.Frame(controls_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

# Left Frame Widgets
tk.Label(
    left_frame,
    text="Left Channel",
    font=("Helvetica", 14, "bold"),
    fg="#415a77",
    bg="#DBDAD6",
).pack(pady=(0, 10))

ttk.Label(left_frame, text="Frequency (Hz):").pack()
frequency_left_entry = ttk.Entry(left_frame, width=10, justify="center")
frequency_left_entry.insert(0, str(frequency_left))
frequency_left_entry.pack(pady=(0, 5))
frequency_left_entry.bind("<FocusOut>", update_frequency_left)
frequency_left_entry.bind("<Return>", update_frequency_left)

frequency_left_slider = ttk.Scale(
    left_frame,
    from_=1,
    to=20000,
    orient="horizontal",
    length=300,
    command=update_frequency_left_slider,
)
frequency_left_slider.set(frequency_left)
frequency_left_slider.pack(pady=(0, 20))

ttk.Label(left_frame, text="Phase (degrees):").pack()
phase_left_entry = ttk.Entry(left_frame, width=10, justify="center")
phase_left_entry.insert(0, str(phase_left))
phase_left_entry.pack(pady=(0, 5))
phase_left_entry.bind("<FocusOut>", update_phase_left)
phase_left_entry.bind("<Return>", update_phase_left)

phase_left_slider = ttk.Scale(
    left_frame,
    from_=0,
    to=360,
    orient="horizontal",
    length=300,
    command=update_phase_left_slider,
)
phase_left_slider.set(phase_left)
phase_left_slider.pack()

# Right Frame Widgets
tk.Label(
    right_frame,
    text="Right Channel",
    font=("Helvetica", 14, "bold"),
    fg="#3a5a40",
    bg="#DBDAD6",
).pack(pady=(0, 10))

ttk.Label(right_frame, text="Frequency (Hz):").pack()
frequency_right_entry = ttk.Entry(right_frame, width=10, justify="center")
frequency_right_entry.insert(0, str(frequency_right))
frequency_right_entry.pack(pady=(0, 5))
frequency_right_entry.bind("<FocusOut>", update_frequency_right)
frequency_right_entry.bind("<Return>", update_frequency_right)

frequency_right_slider = ttk.Scale(
    right_frame,
    from_=1,
    to=20000,
    orient="horizontal",
    length=300,
    command=update_frequency_right_slider,
)
frequency_right_slider.set(frequency_right)
frequency_right_slider.pack(pady=(0, 20))

ttk.Label(right_frame, text="Phase (degrees):").pack()
phase_right_entry = ttk.Entry(right_frame, width=10, justify="center")
phase_right_entry.insert(0, str(phase_right))
phase_right_entry.pack(pady=(0, 5))
phase_right_entry.bind("<FocusOut>", update_phase_right)
phase_right_entry.bind("<Return>", update_phase_right)

phase_right_slider = ttk.Scale(
    right_frame,
    from_=0,
    to=360,
    orient="horizontal",
    length=300,
    command=update_phase_right_slider,
)
phase_right_slider.set(phase_right)
phase_right_slider.pack()

# Volume control (in the center)
volume_frame = ttk.Frame(main_frame)
volume_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 60))

ttk.Label(volume_frame, text="Volume (%)", font=("Helvetica", 12, "bold")).pack()
volume_slider = ttk.Scale(
    volume_frame,
    from_=0,
    to=100,
    orient="horizontal",
    length=200,
    command=update_volume,
)
volume_slider.set(volume * 100)
volume_slider.pack(pady=(10, 5))

# Add a label to display the volume value
volume_value_label = ttk.Label(
    volume_frame, text=f"{int(volume * 100)}%", font=("Helvetica", 10)
)
volume_value_label.pack()

# Button Frame
button_frame = ttk.Frame(main_frame)
button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 30))

# Center align the start and stop buttons
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(3, weight=1)

# Start Button
start_button = ttk.Button(button_frame, text="Start", command=start_stream, width=15)
start_button.grid(row=0, column=1, padx=(0, 10), pady=(0, 20))

# Stop Button
stop_button = ttk.Button(button_frame, text="Stop", command=stop_stream, width=15)
stop_button.grid(row=0, column=2, pady=(0, 20))
stop_button.config(state="disabled")

# Main Menu Setup
menu_bar = tk.Menu(root)
# File Menu
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Save Configuration", command=save_configuration)
file_menu.add_command(label="Load Configuration", command=load_configuration)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
# Help Menu
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About", command=show_about_dialog)
help_menu.add_command(label="Help", command=show_help_dialog)
menu_bar.add_cascade(label="File", menu=file_menu)
menu_bar.add_cascade(label="Help", menu=help_menu)
root.config(menu=menu_bar)

# Set window size
root.geometry(f"{window_width}x{window_height}")

# Center the window on the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Initial plot rendering
plot_waveforms()

root.mainloop()

# Close the database connection when the application exits
conn.close()
