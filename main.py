import tkinter as tk
import requests
from PIL import Image, ImageTk
import numpy as np
import openpyxl
import pandas as pd
from tkinter import messagebox, PhotoImage, filedialog, ttk, Canvas, Label, Toplevel, Frame, Listbox, Entry, Button, Scrollbar, StringVar, END
from pdf_generator import generate_pdf_copy
import ctypes
import threading
import io
try:
   ctypes.windll.shcore.SetProcessDpiAwareness(2)
except AttributeError:
   pass
ctypes.windll.shcore.SetProcessDpiAwareness(1)

nettopris = 0
original_systempris = 0
dialog_open = False
warning_dialog_open = False

# Create the root window before creating any tkinter variables or widgets
root = tk.Tk()
root.title("CheckWatt-ify")
root.iconbitmap('files/solarchoice.ico')

btn_image = PhotoImage(file="files/checkwattify.png")
gron_teknik_var = tk.StringVar(value="Nej")

# Create the frame here, right after creating the root.
frame = tk.Frame(root, padx=25, pady=15)
frame.grid(row=0, column=0, padx=10, pady=10)

# Setting the minimum size for column 1
entry_width = 125  # Replace with your desired width
frame.columnconfigure(1, minsize=entry_width)

kund_namn = tk.StringVar()
kund_efternamn = tk.StringVar()
kund_personnummer = tk.StringVar()
kund_adress = tk.StringVar()
kund_postnummer = tk.StringVar()
kund_stad = tk.StringVar()
kund_fastighetsbeteckning = tk.StringVar()
kund_arsforbrukning = tk.StringVar()
kund_huvudsakring = tk.StringVar()
kund_lantbruksinstallation = tk.BooleanVar()

dialog = None

def close_kunduppgifter_dialog():
    global dialog_open, dialog
    dialog_open = False
    if dialog:
        dialog.destroy()
        dialog = None

def open_kunduppgifter_dialog():
    global dialog_open, dialog
    if dialog_open:
        return
    dialog_open = True
    dialog = tk.Toplevel(root)
    dialog.title("Kunduppgifter")
    dialog.geometry("870x340")  # Updated size to fit the two columns

    # Labels and fields for the first column
    col1_labels = ["Namn", "Efternamn", "Personnummer", " ", "Adress", "Postnummer", "Stad", "Fastighetsbeteckning"]
    col1_vars = [kund_namn, kund_efternamn, kund_personnummer, None, kund_adress, kund_postnummer, kund_stad, kund_fastighetsbeteckning]
    
    # Labels and fields for the second column
    col2_labels = ["Årsförbrukning", "Huvudsäkring", "Lantbruksinstallation"]
    col2_vars = [kund_arsforbrukning, kund_huvudsakring, kund_lantbruksinstallation]

    # Create labels and fields for the first column
    for i, (label, var) in enumerate(zip(col1_labels, col1_vars)):
        if var is None:
            tk.Label(dialog, text="").grid(row=i, column=0, columnspan=2)
        else:
            tk.Label(dialog, text=label).grid(row=i, column=0, padx=10, pady=5)
            tk.Entry(dialog, textvariable=var).grid(row=i, column=1, padx=10, pady=5)

    # Space between columns
    tk.Label(dialog, text="   ").grid(row=0, column=2)

    # Create labels and fields for the second column
    for i, (label, var) in enumerate(zip(col2_labels, col2_vars)):
        tk.Label(dialog, text=label).grid(row=i, column=3, padx=10, pady=5)
        if label == "Lantbruksinstallation":
            tk.Checkbutton(dialog, text="Ja", variable=var).grid(row=i, column=4, padx=10, pady=5)
        else:
            tk.Entry(dialog, textvariable=var).grid(row=i, column=4, padx=10, pady=5)

    dialog.protocol("WM_DELETE_WINDOW", close_kunduppgifter_dialog)

def save_kunduppgifter():
    saved_data = {
        'Namn': kund_namn.get(),
        'Efternamn': kund_efternamn.get(),
        'Personnummer': kund_personnummer.get(),
        'Adress': kund_adress.get(),
        'Postnummer': kund_postnummer.get(),
        'Stad': kund_stad.get(),
        'Fastighetsbeteckning': kund_fastighetsbeteckning.get(),
        'Årsförbrukning': kund_arsforbrukning.get(),
        'Huvudsäkring': kund_huvudsakring.get(),
        'Lantbruksinstallation': kund_lantbruksinstallation.get()
    }

def reset_kunduppgifter():
    # Clear the StringVar variables
    kund_namn.set('')
    kund_efternamn.set('')
    kund_personnummer.set('')
    kund_adress.set('')
    kund_postnummer.set('')
    kund_stad.set('')
    kund_fastighetsbeteckning.set('')
    kund_arsforbrukning.set('')
    kund_huvudsakring.set('')
    
    # Reset the BooleanVar variable (for the checkbox)
    kund_lantbruksinstallation.set(False)

def toggle_button_color(button, var):
    if var.get() == "Ja":
        button.config(bg="#90EE90")  # Green for "Ja"
    else:
        button.config(bg="SystemButtonFace")  # Default color for "Nej"

def reset_values():
    global warning_dialog_open
    if warning_dialog_open:
        return
    warning_dialog_open = True

    answer = messagebox.askquestion("Bekräfta", "Vill du börja om på nytt?")
    
    if answer == 'yes':
        # Reset the values only if the user confirms
        combobox_panels.set("12")
        combobox_battery.set("Välj batteristorlek")
        papptak_var.set("Nej")
        forty_deg_var.set("Nej")
        five_meter_var.set("Nej")
        extra_building_var.set("Nej")
        laddbox_var.set("Nej")
        extra_savings_entry.delete(0, tk.END)
        gron_teknik_combobox.set("Nej")
        discount_var.set(0.0)

        # Reset button colors
        toggle_button_color(papptak_button, papptak_var)
        toggle_button_color(forty_deg_button, forty_deg_var)
        toggle_button_color(five_meter_button, five_meter_var)
        toggle_button_color(extra_building_button, extra_building_var)
        toggle_button_color(laddbox_button, laddbox_var)
        
        # Recalculate prices
        on_num_panels_or_battery_changed()

        reset_kunduppgifter()

    warning_dialog_open = False

# Create and initialize systempris_var and nettopris_var
systempris_var = tk.StringVar(value="")  # Initialize with an empty string or default value
nettopris_var = tk.StringVar(value="")   # Initialize with an empty string or default valuenett

def toggle_button_color(button, var):
    button.config(bg="#90EE90" if var.get() == "Ja" else "SystemButtonFace")

def calculate_total_systempris(num_panels, battery_size):
    # Calculate the base price based on the number of panels
    base_pris = systempris[valid_panel_numbers == int(num_panels)][0]
    
    # Additional costs based on selected options
    additional_costs = 0
    if papptak_var.get() == "Ja":
        additional_costs += papptak_values[valid_panel_numbers == int(num_panels)][0]
    if forty_deg_var.get() == "Ja":
        additional_costs += forty_deg_values[valid_panel_numbers == int(num_panels)][0]
    if five_meter_var.get() == "Ja":
        additional_costs += five_meter_values[valid_panel_numbers == int(num_panels)][0]
    if extra_building_var.get() == "Ja":
        additional_costs += extra_building_values[valid_panel_numbers == int(num_panels)][0]
    if laddbox_var.get() == "Ja":
        additional_costs += fixed_cost  # Add the fixed cost for Laddbox

    reallocation_value = 0
    if battery_size in ["5 kWh", "10 kWh", "15 kWh", "20 kWh"]:
        reallocation_value = 25547  # The reallocation value is considered only if a battery is selected

    # Additional costs based on the selected battery size with a 25% increase (including VAT)
    if battery_size == "5 kWh":
        additional_costs += (42000 * 1.25) + reallocation_value
    elif battery_size == "10 kWh":
        additional_costs += (70000 * 1.25) + reallocation_value
    elif battery_size == "15 kWh":
        additional_costs += (98000 * 1.25) + reallocation_value
    elif battery_size == "20 kWh":
        additional_costs += (112000 * 1.25) + reallocation_value

    return int(base_pris + additional_costs)

def on_num_panels_or_battery_changed(event=None):
    # This function is triggered when either the panel number or battery size is changed
    num_panels = combobox_panels.get()
    battery_size = combobox_battery.get()  # Get the selected battery size
    if num_panels.isdigit() and int(num_panels) in valid_panel_numbers:
        # Calculate the total system price without any decimal places
        pris = int(calculate_total_systempris(num_panels, battery_size))  # Convert to int to remove decimals
        # Format the price with a space as thousands separator
        formatted_pris = f"{int(pris):,}".replace(",", " ")
        systempris_var.set(f"{formatted_pris} SEK")

        # Call the select_and_generate function to update the nettopris
        select_and_generate()

    else:
        messagebox.showerror("Error", "Ogiltigt antal paneler valt. Välj ett nummer mellan 12 och 75.")

def on_option_changed(*args):
    # This function is triggered when any option changes. It recalculates the price without validating panel numbers.
    num_panels = combobox_panels.get()
    battery_size = combobox_battery.get()  # Get the selected battery size
    if num_panels.isdigit() and int(num_panels) in valid_panel_numbers:
        pris = calculate_total_systempris(num_panels, battery_size)  # Pass both num_panels and battery_size
        formatted_pris = f"{pris:,}".replace(",", " ")  # Add space as thousands separator
        systempris_var.set(f"{formatted_pris} SEK")

def update_price_based_on_discount(value):
    """Update the system price based on the discount."""
    discount = float(value)
    discounted_price = original_systempris * (1 - (discount / 100))  # apply discount on original price

    # Update the systempris_var with the new discounted price
    formatted_price = f"{discounted_price:,.0f}".replace(',', ' ')  # format it as you like
    systempris_var.set(f"{formatted_price} SEK")

    # Call select_and_generate to update nettopris based on the new systempris
    select_and_generate()

def create_option(parent, row, label_text, var, fixed_cost=0):
    label = tk.Label(parent, text=label_text)
    label.grid(row=row, column=0, padx=20, pady=5, sticky=tk.W)

    button = tk.Button(
        parent,
        textvariable=var,
        command=lambda: [var.set("Ja" if var.get() == "Nej" else "Nej"), toggle_button_color(button, var)],
        relief="raised",
        width=5,
        bg="#90EE90",  # Set the background color to green
    )
    button.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)

    var.trace("w", on_option_changed)  # Call the function whenever the option changes

    toggle_button_color(button, var)  # Set the initial color

    if fixed_cost > 0:
        var.trace("w", lambda *args: on_laddbox_toggle(fixed_cost))

    return button

# Create a parent frame to hold both the "Påslag" frame and the battery-related frame
parent_frame = ttk.Frame(frame)
parent_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")  # Adjust the sticky parameter

# Set row and column weights so that the parent frame fills the available space
parent_frame.grid_rowconfigure(0, weight=1)
parent_frame.grid_columnconfigure(0, weight=1)

options_group_frame = ttk.LabelFrame(parent_frame, text="Påslag", borderwidth=1, relief="solid", padding=5)
options_group_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

# Create options inside the options_group_frame
papptak_var = tk.StringVar(value="Nej")
papptak_button = create_option(options_group_frame, 0, "Papptak", papptak_var)

forty_deg_var = tk.StringVar(value="Nej")
forty_deg_button = create_option(options_group_frame, 2, "40 grader+", forty_deg_var)

five_meter_var = tk.StringVar(value="Nej")
five_meter_button = create_option(options_group_frame, 3, "5 meter+", five_meter_var)

extra_building_var = tk.StringVar(value="Nej")
extra_building_button = create_option(options_group_frame, 4, "Extra byggnad", extra_building_var)

laddbox_var = tk.StringVar(value="Nej")
fixed_cost = 20000  # Fixed cost for Laddbox
laddbox_button = create_option(options_group_frame, 1, "Laddbox", laddbox_var, fixed_cost=fixed_cost)

# Add the following lines after creating the above variables
# Call the select_and_generate function when any option changes
papptak_var.trace("w", lambda *args: select_and_generate())
forty_deg_var.trace("w", lambda *args: select_and_generate())
five_meter_var.trace("w", lambda *args: select_and_generate())
extra_building_var.trace("w", lambda *args: select_and_generate())
laddbox_var.trace("w", lambda *args: select_and_generate())

# Define combobox_battery here
combobox_battery = ttk.Combobox(parent_frame, values=["5 kWh", "10 kWh", "15 kWh", "20 kWh"], state="readonly", width=8)

# Place a label to indicate the purpose of the combobox and center it
battery_label = tk.Label(parent_frame, text="Batteristorlek:", justify="center")
battery_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

# Place the combobox_battery widget in the grid, centered within columns 0 and 1
combobox_battery.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
combobox_battery.set("Välj batteristorlek")

# Configure the parent frame's rows and weights
parent_frame.grid_rowconfigure(0, weight=1)  # "Påslag" frame
parent_frame.grid_rowconfigure(1, weight=1)  # Battery-related frame
parent_frame.grid_rowconfigure(2, weight=1)  # "Besparing Open Solar" frame

# Load spreadsheet
xl = pd.ExcelFile('files/priser.xlsx')

# Load a sheet into a DataFrame by name
df1 = xl.parse('pris')

# Extract the range of valid panel numbers and corresponding prices
valid_panel_numbers = df1.iloc[2:68, 2].values  # Adjust if your DataFrame's indexing doesn't start from 0
systempris = df1.iloc[2:67, 5].values
papptak_values = 1.25 * df1.iloc[2:67, 7].values
forty_deg_values = 1.25 * df1.iloc[2:67, 8].values
five_meter_values = 1.25 * df1.iloc[2:67, 9].values
extra_building_values = 1.25 * df1.iloc[2:67, 10].values

# Convert NaN and inf to 0, then to int
papptak_values = np.nan_to_num(papptak_values, nan=0, posinf=0, neginf=0).astype(int)
forty_deg_values = np.nan_to_num(forty_deg_values, nan=0, posinf=0, neginf=0).astype(int)
five_meter_values = np.nan_to_num(five_meter_values, nan=0, posinf=0, neginf=0).astype(int)
extra_building_values = np.nan_to_num(extra_building_values, nan=0, posinf=0, neginf=0).astype(int)
systempris = np.nan_to_num(systempris, nan=0, posinf=0, neginf=0).astype(int)

systempris = np.nan_to_num(systempris, nan=0, posinf=0, neginf=0).astype(int)  # Convert NaN and inf to 0, then to int

def on_laddbox_toggle(fixed_cost):
    if laddbox_var.get() == "Ja":
        laddbox_button.config(bg="#90EE90")  # Light Green for Ja
    else:
        laddbox_button.config(bg="SystemButtonFace")  # Default color for Nej

def format_price(price):
    """Format the price with a space before the last 3 numbers."""
    return price[:-3] + " " + price[-3:]

# Update the on_option_changed function to call select_and_generate
def on_option_changed(*args):
    select_and_generate()
    pris = calculate_total_systempris(num_panels, battery_size)  # Already an int now
    formatted_pris = f"{pris:,}".replace(",", " ")  # Add space as thousands separator
    systempris_var.set(f"{formatted_pris} SEK")

def select_and_generate():
    global nettopris
    num_panels = combobox_panels.get()
    battery_size = combobox_battery.get()
    gron_teknik_selection = gron_teknik_combobox.get()

    if not num_panels.isdigit() or int(num_panels) not in valid_panel_numbers:
        messagebox.showerror("Error", "Ogiltigt antal paneler valt. Välj ett nummer mellan 12 och 75.")
        return

    panel_cost = systempris[valid_panel_numbers == int(num_panels)][0]
    papptak_cost = papptak_values[valid_panel_numbers == int(num_panels)][0] if papptak_var.get() == "Ja" else 0
    forty_deg_cost = forty_deg_values[valid_panel_numbers == int(num_panels)][0] if forty_deg_var.get() == "Ja" else 0
    five_meter_cost = five_meter_values[valid_panel_numbers == int(num_panels)][0] if five_meter_var.get() == "Ja" else 0
    extra_building_cost = extra_building_values[valid_panel_numbers == int(num_panels)][0] if extra_building_var.get() == "Ja" else 0
    laddbox_cost = fixed_cost if laddbox_var.get() == "Ja" else 0

    toggle_button_color(papptak_button, papptak_var)
    toggle_button_color(forty_deg_button, forty_deg_var)
    toggle_button_color(five_meter_button, five_meter_var)
    toggle_button_color(extra_building_button, extra_building_var)
    toggle_button_color(laddbox_button, laddbox_var)

    reallocation_value = 0
    if battery_size in ["5 kWh", "10 kWh", "15 kWh", "20 kWh"]:
        reallocation_value = 25547

    # Calculate the battery_cost including the reallocation value.
    if battery_size == "5 kWh":
        battery_cost = 42000 * 1.25
    elif battery_size == "10 kWh":
        battery_cost = 70000 * 1.25
    elif battery_size == "15 kWh":
        battery_cost = 98000 * 1.25
    elif battery_size == "20 kWh":
        battery_cost = 112000 * 1.25
    else:
        battery_cost = 0  # If no battery is selected, the cost remains 0

    # Aggregate costs before discount
    total_panel_related_cost = panel_cost + papptak_cost + forty_deg_cost + five_meter_cost + extra_building_cost
    total_battery_related_cost = laddbox_cost + battery_cost + reallocation_value

    # Calculate the discount for systempris
    discount_percentage = discount_var.get() / 100
    discount_multiplier = 1 - discount_percentage

    # Calculate the total cost before and after discount
    original_total_cost = total_panel_related_cost + total_battery_related_cost
    discounted_total_cost = original_total_cost * discount_multiplier

    # Calculate the potential "Grön teknik" discounts based on the discounted total cost
    solar_solution_discount = (total_panel_related_cost * discount_multiplier) * 0.194
    battery_laddbox_discount = (total_battery_related_cost * discount_multiplier) * 0.485

    # Sum up the potential discounts
    total_potential_discount = solar_solution_discount + battery_laddbox_discount

    # Format and set systempris_var with the discounted_total_cost
    formatted_systempris = f"{int(discounted_total_cost):,}".replace(",", " ")
    systempris_var.set(f"{formatted_systempris} SEK")

    # If "Grön teknik" is "Nej", there are no discounts, and nettopris should be equal to the discounted total cost.
    if gron_teknik_selection == "Nej":
        nettopris = discounted_total_cost
    else:
        # Determine the cap based on the gron_teknik_selection
        cap = total_potential_discount
        if gron_teknik_selection == "1 person":
            cap = min(50000, total_potential_discount)
        elif gron_teknik_selection == "2 personer":
            cap = min(100000, total_potential_discount)

        # The actual discount is the lesser of the total potential discount or the cap.
        actual_discount = min(total_potential_discount, cap)

        # Calculate nettopris by subtracting the actual discount from the discounted total cost
        nettopris = discounted_total_cost - actual_discount

    # Round nettopris to the nearest whole number and update the GUI element
    nettopris = round(nettopris)
    nettopris_value = "{:,}".format(nettopris).replace(",", " ")
    nettopris_var.set(f"{nettopris_value} SEK")

def check_panel_selection(event=None):
    # Check if the selected number of panels is valid (adjust the condition as necessary)
    if combobox_panels.get().isdigit() and int(combobox_panels.get()) in valid_panel_numbers:
        rabatt_scale.config(state=tk.NORMAL)  # Enable the slider
    else:
        rabatt_scale.config(state=tk.DISABLED)  # Disable the slider

def generate_pdf():
    # This function is triggered when the user clicks the button to generate the PDF.

    # Initialize output_path to an empty string
    output_path = ""

    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        # Assuming you've stored the necessary data (like battery size, extra savings, etc.) globally or in some accessible manner,
        # you can now pass this data to your PDF generation function.

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if output_path:
            # Get the selected battery size
            battery_size = combobox_battery.get()

            # Get the extra savings value from the entry
            extra_savings = extra_savings_entry.get()

            # Convert systempris_var and nettopris_var to appropriate types
            systempris_value = int(''.join(filter(str.isdigit, systempris_var.get())))
            nettopris_value = nettopris

            # Get the value of laddbox_var
            laddbox_selected = laddbox_var.get()

            # Call the PDF generation function with all the required values
            generate_pdf_copy(file_path, output_path, systempris_value, nettopris_value, battery_size, extra_savings, laddbox_selected)

def on_combobox_changed(event=None):
    on_num_panels_or_battery_changed(event)
    check_panel_selection(event)

# Define validate_cmd before creating extra_savings_entry
def validate_input(value, max_length):
    if value == "":
        return True
    if not value.isdigit():
        return False
    if len(value) > int(max_length):
        return False
    return True

validate_cmd = root.register(validate_input)

def open_design_window():
    design_window = Toplevel()
    design_window.title("Design Tool")

    content_frame = Frame(design_window, padx=20, pady=20)
    content_frame.pack(expand=True, fill='both')

    # Set the size of the window to be 50 pixels wider and 20 pixels taller than some base size
    base_width = 300  # The base width for your window
    base_height = 270  # The base height for your window
    design_window.geometry(f"{base_width + 50}x{base_height + 20}")

    address_var = StringVar()
    address_label = Label(content_frame, text="Enter Address:")
    address_label.pack(pady=(10, 0))

    address_entry = Entry(content_frame, textvariable=address_var)
    address_entry.pack(pady=5)

    # Create a frame to control the size of the Listbox
    listbox_frame = Frame(content_frame, width=280, height=100)
    listbox_frame.pack_propagate(False)  # Prevent the frame from resizing to fit its contents
    listbox_frame.pack(pady=5)  # This will pack the frame below the address_entry

    suggestions_listbox = Listbox(listbox_frame)
    suggestions_listbox.pack(fill='both', expand=True)

    after_id = None

    def update_suggestions(sv, listbox):
        input_text = sv.get().strip()
        listbox.delete(0, END)  # Clear existing suggestions
        if input_text:  # Only make a request if there is input
            # Move the request to a background thread
            threading.Thread(target=lambda: fetch_suggestions(input_text, listbox)).start()

    def fetch_suggestions(input_text, listbox):
        try:
            autocomplete_url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={input_text}&types=geocode&key=YOUR_API_KEY"
            response = requests.get(autocomplete_url)
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
            suggestions = response.json()

            # Check if the main thread is still active
            if threading.main_thread().is_alive():
                # Loop through the predictions and add them to the listbox
                for prediction in suggestions.get('predictions', []):
                    design_window.after(0, lambda p=prediction: listbox.insert(END, p['description']))
        except requests.RequestException as e:
            print(f"Request error: {e}")

    def debounce(fn, wait=350):
        nonlocal after_id  # Declare after_id as nonlocal to access the variable defined in open_design_window
        if after_id is not None:
            design_window.after_cancel(after_id)
        after_id = design_window.after(wait, fn)

    address_var.trace('w', lambda name, index, mode, sv=address_var: debounce(lambda: update_suggestions(sv, suggestions_listbox)))

    def select_address(address, parent_window):
        api_key = 'AIzaSyCm79VBrHtG1wSx3FmaWNJ9p53QgpfCcls'
        # The maximum allowed size for standard API access is 640x640
        desired_width = 640
        desired_height = 640
        url = f"https://maps.googleapis.com/maps/api/staticmap?center={address}&zoom=18&size={desired_width}x{desired_height}&maptype=satellite&key={api_key}"

        # Fetch the image from the URL
        response = requests.get(url)
        
        print("Status Code:", response.status_code)  # Debugging line
        if response.status_code != 200:
            print("Response Content:", response.text)  # Debugging line
            return  # Exit the function if there was an error

        img_data = response.content

        # Display the image in a new window using a Label
        image_window = Toplevel(parent_window)
        image_window.title("Satellite Image")
        image_window.geometry(f'{desired_width}x{desired_height}')  # Set the geometry to match the desired size

        try:
            img = Image.open(io.BytesIO(img_data))
            img_photo = ImageTk.PhotoImage(img)
            img_label = Label(image_window, image=img_photo)
            img_label.image = img_photo  # Keep a reference
            img_label.pack(expand=True, fill='both')
        except Exception as e:
            print("Error displaying the image:", e)  # Set the geometry to match the desired size

        img = Image.open(io.BytesIO(img_data))
        img_photo = ImageTk.PhotoImage(img)

        img_label = Label(image_window, image=img_photo)
        img_label.image = img_photo  # Keep a reference, so it

    select_button = Button(design_window, text="Select", command=lambda: select_address(suggestions_listbox.get(suggestions_listbox.curselection()), design_window))
    select_button.pack(pady=(5, 10))

common_width = 15

# Place "Besparing Open Solar" label and entry in the main frame
extra_savings_label = tk.Label(frame, text="Besparing Open Solar")
extra_savings_label.grid(row=4, column=0, pady=5, sticky=tk.W)
extra_savings_entry = tk.Entry(frame, validate="key", validatecommand=(validate_cmd, "%P", "5"), width=common_width)
extra_savings_entry.grid(row=4, column=1, pady=5, sticky=tk.W)

kunduppgifter_button = tk.Button(frame, text="Kunduppgifter", command=open_kunduppgifter_dialog)
kunduppgifter_button.grid(row=0, column=0, pady=10)

refresh_icon = "🔄"  # Unicode character for refresh icon
refresh_button = tk.Button(frame, text=refresh_icon, font=("Arial", 18), command=reset_values)
refresh_button.grid(row=0, column=1, pady=5, sticky=tk.E)

# Convert the range of valid panel numbers to a list of strings for the combobox
panel_numbers_list = valid_panel_numbers.astype(str).tolist()

panel_label = tk.Label(frame, text="Antal Paneler:")
panel_label.grid(row=1, column=0, pady=5, sticky=tk.W)  # Aligned to the West (left)

combobox_panels = ttk.Combobox(frame, values=panel_numbers_list, state="readonly", width=15)
combobox_panels.grid(row=1, column=1, pady=10)  # Next to the label
combobox_panels.set("12")  # Default text

combobox_panels.bind('<<ComboboxSelected>>', on_combobox_changed)
# Ensure this line is in your code, binding the combobox change event to the handler
combobox_battery.bind('<<ComboboxSelected>>', on_num_panels_or_battery_changed)

# First, create the Label for the discount
rabatt_label = tk.Label(frame, text="Rabatt:")
rabatt_label.grid(row=6, column=0, pady=5, sticky=tk.W)  # Adjusted row number
# Create a variable to hold the discount percentage
discount_var = tk.DoubleVar()  # This variable will hold the discount percentage
# Create the Scale for the discount percentage
rabatt_scale = tk.Scale(frame, from_=0, to=10, resolution=0.1, orient=tk.HORIZONTAL, variable=discount_var, length=common_width * 8)  # The Scale widget's width is controlled by the 'length' parameter and it's in pixels
rabatt_scale.grid(row=6, column=1, pady=5, sticky=tk.W)

# Now, link the update function to the discount slider
rabatt_scale.config(command=update_price_based_on_discount)
# Finally, place the rabatt_scale in the grid

# Create a label for "Systempris inkl. moms" and grid it
systempris_label = tk.Label(frame, text="Systempris inkl. moms:")
systempris_label.grid(row=7, column=0, pady=(10, 0), sticky=tk.W)  # changed to sticky West for left alignment

# Create a label to display the actual system price and grid it
systempris_value_label = tk.Label(frame, textvariable=systempris_var) 
systempris_value_label.grid(row=7, column=1, pady=(10, 0), sticky=tk.W)  # sticky West for left alignment

# Assuming the "grön teknik" combobox is placed in row 4 (you should check this)
gron_teknik_label = tk.Label(frame, text="Grön Teknik:")
gron_teknik_label.grid(row=5, column=0, pady=5, sticky=tk.W)
gron_teknik_combobox = ttk.Combobox(frame, values=["Nej", "1 person", "2 personer"], state="readonly", width=common_width, textvariable=gron_teknik_var)
gron_teknik_combobox.grid(row=5, column=1, pady=(10, 0), sticky=tk.W)
gron_teknik_combobox.set("Nej")  # Default selection
gron_teknik_combobox.bind('<<ComboboxSelected>>', lambda e: select_and_generate())

# Create a label for "Nettopris efter avdrag" and grid it
nettopris_label = tk.Label(frame, text="Nettopris efter avdrag:")
nettopris_label.grid(row=8, column=0, padx=(0, 10), sticky=tk.W)  # consistent with Systempris, added padding on the right

# Create a label to display the calculated Nettopris and grid it
nettopris_value_label = tk.Label(frame, textvariable=nettopris_var)
nettopris_value_label.grid(row=8, column=1, sticky=tk.W)  # Directly below Systempris value, aligned to the left

btn_image = PhotoImage(file="files/checkwattify.png")
btn_select = tk.Button(frame, image=btn_image, command=generate_pdf)
btn_select.grid(row=12, column=0, columnspan=2, pady=10)

design_button = tk.Button(frame, text="Design", command=open_design_window)
design_button.grid(row=13, column=0, columnspan=2, pady=10)  # Adjust the row and column as needed

copyright_label = tk.Label(frame, text="CheckWatt-ify © Version beta 0.45", font=("Arial", 7), anchor='center')  # anchor set to 'center'
copyright_label.grid(row=13, column=0, columnspan=2, pady=5, sticky='ew')  # sticky set to 'ew'

# Make sure to update the UI so that Tkinter calculates the actual size needed for each widget
frame.update_idletasks()

# Get the width of the Entry widget for "Besparing Open Solar"
entry_width = extra_savings_entry.winfo_reqwidth()

# Set the width of the Combobox for "Grön Teknik" and the Scale for "Rabatt" based on the Entry widget's width
gron_teknik_combobox.config(width=int(entry_width // 8))  # Width in terms of characters
rabatt_scale.config(length=entry_width)  # Width in terms of pixels

check_panel_selection()
root.mainloop()
