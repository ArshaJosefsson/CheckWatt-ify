from PyPDF2 import PdfWriter, PdfReader, PdfMerger
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib.colors import white, black, red
from reportlab.platypus import Image
from reportlab.lib.colors import HexColor
import io
from io import BytesIO

font_name = "Roboto-Regular"
font_path = "files/Roboto-Regular.ttf"
pdfmetrics.registerFont(TTFont(font_name, font_path))
bold_font_name = "Roboto-Bold"
bold_font_path = "files/Roboto-Bold.ttf"
pdfmetrics.registerFont(TTFont(bold_font_name, bold_font_path))

def format_number(number):
            """Format the number with a space before the last 3 digits."""
            str_num = str(number)
            return str_num[:-3] + " " + str_num[-3:]

def draw_investment_graph(can, initial_investment, yearly_savings, x_start, y_start, width, height):
    # Constants for the graph
    years = 30
    gap = 5
    bar_width = width / years - gap  # Subtract for the gap between bars
    
    # Colors
    gray_color = HexColor("#D1D2D4")
    green_color = HexColor("#0E5742")
    line_color = HexColor("#A9A9A9")  # Slightly transparent gray for the lines
    
    # Add currency values on the y-axis from -300,000 to 700,000 and draw grid lines
    y_values = list(range(-300000, 800000, 100000))
    for y_val in y_values:
        y_position = y_start + y_val * height / 1000000  # Adjusting to the scale of 1 unit = 100,000 SEK
        can.setFont(font_name, 10)
        can.setFillColor(black)
        can.drawString(x_start - 80, y_position - 5, f"SEK {y_val:,}".replace(",", " "))
        
        # Draw light gray horizontal lines for every y-value
        can.setStrokeColorRGB(0.7, 0.7, 0.7, 0.5)  # Make lines more transparent
        can.line(x_start, y_position, x_start + width, y_position)

    # Calculate the "Återbetalningstid" based on the initial savings amount
    payback_year = initial_investment / yearly_savings

    accumulated_savings = 0
    for year in range(1, years + 1):
        accumulated_savings += yearly_savings
        x_position = x_start + (year - 1) * (bar_width + gap)

        # Reduce savings by X% after year 5
        if year > 6:
            accumulated_savings *= 0.973

        # Determine if the bar is gray or green
        if accumulated_savings <= initial_investment:
            bar_color = gray_color
            bar_height = -initial_investment + accumulated_savings
        else:
            bar_color = green_color
            bar_height = accumulated_savings - initial_investment

        # Draw the bar
        can.setFillColor(bar_color)
        can.rect(x_position, y_start, bar_width, bar_height * height / 1000000, fill=True, stroke=False)

        # Add year labels below each bar only for years 1, 5, 10, 15, 20, 25, 30
        if year in [1, 5, 10, 15, 20, 25, 30]:
            can.setFont(font_name, 10)
            can.setFillColor(black)
            can.drawCentredString(x_position + bar_width / 2, y_start + (-300000 * height / 1000000) - 20, str(year))

    # Draw the 0 SEK line in the middle of the graph
    can.setStrokeColor(black)
    can.line(x_start, y_start, x_start + width, y_start)
    can.drawString(x_start - 60, y_start - 5, "0 SEK")
    
    # Identify and annotate the payback year
    payback_line_length = height / 14  # Half the previous length

    # Setting the line to be semi-transparent
    can.setStrokeColorRGB(0, 0, 0, 0.5)  # Here, the last value is the alpha, making it semi-transparent

    payback_line_x = x_start + payback_year * (bar_width + gap)
    can.line(payback_line_x, y_start - payback_line_length, payback_line_x, y_start)

    # Adjusting the x-coordinate for the text to be 10 pixels to the right
    can.drawString(payback_line_x + 6, y_start - payback_line_length, f"Återbetalningstid {payback_year:.1f} år")
    
    return can

def generate_pdf_copy(input_path, output_path, systempris_value, nettopris_value, battery_size, extra_savings, laddbox_selected):
    savings_increase = {
        "5 kWh": 8670,
        "10 kWh": 17340,
        "15 kWh": 26010,
        "20 kWh": 34680,
    }

    # Use systempris_value instead of systempris
    moms_value = int(systempris_value) * 0.2

    # Process systempris_value only if it's not already an integer
    if not isinstance(systempris_value, int):
        try:
            systempris_value = int(''.join(filter(str.isdigit, str(systempris_value))))
        except ValueError:
            # Handle the case where systempris_value cannot be converted to an integer
            print("Invalid systempris_value:", systempris_value)
            return

    # Convert nettopris_value to string and then perform the 'replace' operations
    nettopris_str = str(nettopris_value)
    nettopris_str_cleaned = nettopris_str.replace("SEK", "").replace(",", "").replace(" ", "").strip()

    # Attempt to convert nettopris_str_cleaned to a float and round it to the nearest integer
    try:
        nettopris = round(float(nettopris_str_cleaned))
    except ValueError:
        # If a ValueError occurs, print an error message and perhaps set nettopris to a default value
        print(f"Invalid nettopris_value: '{nettopris_value}'. It should be a number.")
        nettopris = 0

    # Open the original PDF
    f_in = open(input_path, "rb")
    reader = PdfReader(f_in)

    # Open the additional PDF
    add_file = open("files/CheckWatt.pdf", "rb")
    additional_pdf = PdfReader(add_file)

    # Open the orderflow.pdf for replacing the 8th page
    orderflow_file = open("files/orderflow.pdf", "rb")
    orderflow_pdf = PdfReader(orderflow_file)

    # Open the eib.pdf for replacing the 8th page
    eib_file = open("files/eib.pdf", "rb")
    eib_pdf = PdfReader(eib_file)

    writer = PdfWriter()

    # Process the first page separately to add the image
    first_page = reader.pages[0]
    packet_img = io.BytesIO()
    can_img = canvas.Canvas(packet_img, pagesize=letter)
    img = Image("files/villaagarna.png")
    img.drawHeight = 85  # Set height
    img.drawWidth = 85  # Set width
    img.drawOn(can_img, 500, 600)  # Set x, y coordinates
    can_img.save()
    packet_img.seek(0)
    new_pdf_img = PdfReader(packet_img)

    # Merge the image directly onto the first page
    first_page.merge_page(new_pdf_img.pages[0])
    writer.add_page(first_page)  # Add the merged first page to the writer

    insert_position = 3

    for page_num in range(1, len(reader.pages)):
        page = reader.pages[page_num]

        # If it's the second page
        if page_num == 1:
            total_savings = savings_increase[battery_size] + int(extra_savings)
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

             # Variables for rectangles
            rect_width = 116
            rect_height = 40

            # For Systempris inkl. moms
            rect_x = 310
            rect_y = 680
            formatted_systempris = "SEK {:,}".format(int(systempris_value)).replace(",", " ")
            can.setStrokeColor(white)
            can.setFillColor(white)
            can.rect(rect_x, rect_y, rect_width, rect_height, fill=1)
            can.setFont(font_name, 19)
            can.setFillColor(black)
            can.drawString(rect_x, rect_y + 4, formatted_systempris)  # Adjusted the position slightly

            # For Nettopris efter avdrag
            rect_x = 445
            rect_y = 680
            formatted_nettopris = "SEK {:,}".format(int(nettopris_value)).replace(",", " ")
            can.setStrokeColor(white)
            can.setFillColor(white)
            can.rect(rect_x, rect_y, rect_width, rect_height, fill=1)
            can.setFont(font_name, 19)
            can.setFillColor(black)
            can.drawString(rect_x, rect_y + 4, formatted_nettopris)  # Adjusted the position slightly

            rect_x = 170
            rect_y = 680
            rect_width = 114
            rect_height = 40

            can.setStrokeColor(white)
            can.setFillColor(white)
            can.rect(rect_x, rect_y, rect_width, rect_height, fill=1)

            # New whiteout
            new_rect_y = rect_y - rect_height - 5
            new_rect_width = 100
            can.rect(rect_x, new_rect_y, new_rect_width, rect_height, fill=1)

            # New text on the new whiteout
            can.setFont(font_name, 9)
            can.setFillColor(black)
            can.drawString(rect_x + 9, new_rect_y + 29, "Estimerad årlig ersättning")

            can.setFont(font_name, 19)
            can.setFillColor(black)
            formatted_savings = "SEK {:,}*".format(total_savings).replace(",", " ")
            can.drawString(rect_x + 12, rect_y + 4, formatted_savings)

            # Later in your drawing method or function:
            can.setFont(font_name, 8)
            formatted_extra_savings = format_number(extra_savings)
            formatted_savings_increase = format_number(savings_increase[battery_size])
            note = f"*Ersättningen är uppdelad i två delar; {formatted_extra_savings} kr per år från solenergi och {formatted_savings_increase} kr per år från CheckWatt."
            note_x = 29
            note_y = 609
            can.drawString(note_x, note_y, note)

            can.setFont(font_name, 11)
            note = f"+ Smartmätare"
            note_x = 374
            note_y = 296
            can.drawString(note_x, note_y, note)
                
            can.setFont(font_name, 8)
            note = f"1 x Growatt smartmätare 3 fas"
            note_x = 309
            note_y = 251
            can.drawString(note_x, note_y, note)

            if laddbox_selected == "Ja":
                can.setFont(font_name, 11)
                note = f"+ CheckWatt (se nästa sida)"
                note_x = 348
                note_y = 219
                can.drawString(note_x, note_y, note)

                can.setFont(font_name, 8)
                note = f"1 x CM10 CheckWatt-installation (värde 15 590 SEK)"
                note_x = 309
                note_y = 173
                can.drawString(note_x, note_y, note)
            else:

                img = Image("files/checkwatt_produkt.png")
                img.drawHeight = 84  # Set height
                img.drawWidth = 260  # Set width
                img.drawOn(can, 29, 157)  # Set x, y coordinates

            # Whiteout för total systemeffekt
            whiteout_x = 74
            whiteout_y = 267  # Adjusted to be 5 pixels lower
            whiteout_width = 78
            whiteout_height = 7 + 6  # Increased height by 10 pixels
            can.setFillColor(white)
            can.rect(whiteout_x, whiteout_y, whiteout_width, whiteout_height, fill=True, stroke=False)

            # Note "Total systemeffekt"
            can.setFont(font_name, 8)
            can.setFillColor(black)
            note = "Total systemeffekt"
            can.drawString(whiteout_x+2, whiteout_y + 6, note)  # Adjusted y-coordinate to be 5 pixels above the whiteout's starting y position

            can.save()

            packet.seek(0)
            new_pdf = PdfReader(packet)
            page.merge_page(new_pdf.pages[0])

        # If it's the 3th page
        if page_num == 2:
            packet_fifth = io.BytesIO()
            can_fifth = canvas.Canvas(packet_fifth, pagesize=letter)

            whiteout_x_start = 5  # Set this to your desired starting x-coordinate
            whiteout_y_start = 250
            whiteout_width = 1000
            whiteout_height = 505
            can_fifth.setStrokeColor(white)
            can_fifth.setFillColor(white)
            can_fifth.rect(whiteout_x_start, whiteout_y_start, whiteout_width, whiteout_height, fill=1, stroke=1)

            # Graph position and size (adjust as necessary)
            graph_x_start = 110
            graph_y_start = 460
            graph_width = 450
            graph_height = 280
            
            total_savings = savings_increase[battery_size] + int(extra_savings)
            draw_investment_graph(can_fifth, int(nettopris), total_savings, graph_x_start, graph_y_start, graph_width, graph_height)

            can_fifth.setFont(font_name, 16)
            note = f"Finansiell överblick & återbetalningstid"
            note_x = 163
            note_y = 720
            can_fifth.drawString(note_x, note_y, note)

            light_gray = (0.4, 0.4, 0.4)  # RGB values for a light gray
            transparency = 0.85  # Adjust as needed

            can_fifth.setFont(font_name, 8)
            line_spacing = 3  # Space between lines in pixels
            note_lines = [
                f"• Uträkningen tar hänsyn till det faktum att stödtjänster gentemot Svenska kraftnät (SVK) förväntas bli",
                f"  mindre lönsamma över tid ju fler enheter som kopplar upp sig till CheckWatt och liknande tjänster.",
                f"",
                f"• Denna kalkyl är en estimering med bland annat hänsyn till CheckWatts nuvarande uträkning för",
                f"  lönsamheten av stödtjänster gentemot Svenska kraftnät (SVK). Senast uppdaterad 2023-10-30.",
                f"",
                f"• Beräkningarna tar inte hänsyn till kostnader för utbyte av utrustning som inte omfattas av en garanti.",
                f"  Komponenter kan behöva bytas ut efter garantiperioden."
            ]
            note_x = 27
            note_y = 325

            # Set the text color to light gray and semi-transparent
            can_fifth.setFillColorRGB(*light_gray, transparency)

            for line in note_lines:
                can_fifth.drawString(note_x, note_y, line)
                note_y -= (7 + line_spacing)
            
            can_fifth.save()
            packet_fifth.seek(0)
            new_pdf_fifth = PdfReader(packet_fifth)
            page.merge_page(new_pdf_fifth.pages[0])

            # Create a PDF in memory with the Elpriser image
            packet_elpriser = io.BytesIO()
            can_elpriser = canvas.Canvas(packet_elpriser, pagesize=letter)
            img_elpriser = Image("files/Elpriser.png")  # Make sure the path to Elpriser.png is correct
            img_elpriser.drawHeight = 842  # Set height as needed
            img_elpriser.drawWidth = 595  # Set width as needed
            img_elpriser.drawOn(can_elpriser, 0, 0)  # Set x, y coordinates to the bottom-left corner
            can_elpriser.save()

            # Prepare the Elpriser page for merging
            packet_elpriser.seek(0)
            new_pdf_elpriser = PdfReader(packet_elpriser)

            # Merge the new PDF (from Elpriser.PNG) onto the 3rd page
            page.merge_page(new_pdf_elpriser.pages[0])

            # If it's the 7th page
        if page_num == 3:
            packet_sixth = io.BytesIO()
            can_sixth = canvas.Canvas(packet_sixth, pagesize=letter)
            move_down = -3

            # Define the light gray color with transparency
            light_gray = (0.55, 0.55, 0.55)  # RGB values for a light gray
            transparency = 0.8  # Adjust as needed

            can_sixth.setFont(font_name, 7)
            line_spacing = 3  # Space between lines in pixels
            note_lines = [
                f"Efter hembesöket och en optimering av din solcellsanläggning kan vi eventuellt behöva justera antalet paneler för en säker installation. Om förändringen är",
                f"inom +/- 3 solpaneler justeras priset automatiskt med 4 500 kr/panel. Justeringar som överstiger +/- 3 solpaneler kräver nytt skriftligt godkännande av kund.",
            ]
            note_x = 28
            note_y = 404 + move_down

            # Set the text color to light gray and semi-transparent
            can_sixth.setFillColorRGB(*light_gray, transparency)

            for line in note_lines:
                can_sixth.drawString(note_x, note_y, line)
                note_y -= (7 + line_spacing)

            # Offset coordinates if Laddbox is selected
            y_offset = -5 if laddbox_selected == "Ja" else 0

            # Adjusted Y-coordinate
            note_y = 406 + move_down

            # For Systempris inkl. moms
            rect_x_7th = 212
            rect_y_7th = 590 + y_offset + move_down

            # Variables for whiteout size
            whiteout_width = 250  # Adjust this as needed
            whiteout_height = 15  # Adjust this as needed

            # Whiteout for Systempris inkl. moms
            can_sixth.setStrokeColor(white)
            can_sixth.setFillColor(white)
            can_sixth.rect(rect_x_7th, rect_y_7th, whiteout_width, whiteout_height, fill=1)

            # Calculate X
            moms_value = int(systempris_value) * 0.2

            # Coordinates for "Systempris inkl. moms"
            systempris_x = rect_x_7th
            systempris_y = rect_y_7th + 4

            # Draw Systempris inkl. moms
            formatted_systempris_7th = "SEK {:,}.00".format(int(systempris_value)).replace(",", " ").replace(".", ",")
            can_sixth.setFont(font_name, 10)
            can_sixth.setFillColor(black)
            can_sixth.drawString(systempris_x, systempris_y, formatted_systempris_7th)

            # Calculate the width of the previously drawn text to position the next text correctly
            text_width = pdfmetrics.stringWidth(formatted_systempris_7th, font_name, 10)

            # Coordinates for "inklusive X MOMS"
            moms_x = systempris_x + text_width + 5  # +5 for a little space between the two texts
            moms_y = systempris_y  # No need to add y_offset since systempris_y already has it

            # Format the moms_value to have a space after the second number
            formatted_moms_value = "{:,.2f}".format(moms_value).replace(",", " ").replace(".", ",")

            # Draw the "inklusive X MOMS" in a different size
            text_color = (0, 0, 0, 0.5)
            can_sixth.setFillColorRGB(*text_color)
            can_sixth.setFont(font_name, 8)
            can_sixth.drawString(moms_x, moms_y, f"inklusive SEK {formatted_moms_value} MOMS")

            # Additional whiteout for Systempris - Nettopris
            diff_x = 465
            diff_y = 468 + move_down

            # Approximate width and height based on your other block of code
            diff_text_width = 80  # this is an approximation; adjust based on your actual text width
            diff_text_height = 20  # this is an approximation; adjust based on your font size

            # Calculate whiteout dimensions
            whiteout_diff_x = diff_x - 6
            whiteout_diff_y = diff_y - 5
            whiteout_diff_width = diff_text_width + 10
            whiteout_diff_height = diff_text_height

            # Whiteout the area
            can_sixth.setStrokeColor(white)
            can_sixth.setFillColor(white)
            can_sixth.rect(whiteout_diff_x, whiteout_diff_y, whiteout_diff_width, whiteout_diff_height, fill=1)

            # Calculate Systempris - Nettopris
            diff_value = int(systempris_value) - int(nettopris)

            # Print for debugging purposes
            print(f"Systempris: {systempris_value}, Nettopris: {nettopris}, Difference: {diff_value}")

            # Format and draw Systempris - Nettopris
            formatted_diff = "SEK {:,}.00".format(int(diff_value)).replace(",", " ").replace(".", ",")
            can_sixth.setFont(font_name, 10)  # Using the bold font from the second block
            can_sixth.setFillColor(black)
            can_sixth.drawString(diff_x, diff_y, formatted_diff)  # No need for the +4 adjustment as the position is already approximated from the other block

            # Additional whiteout as per your request
            large_whiteout_width = 700
            large_whiteout_height = 40
            large_whiteout_x = 10
            large_whiteout_y = 536 + y_offset + 1 + move_down
            can_sixth.setStrokeColor(white)
            can_sixth.setFillColor(white)
            can_sixth.rect(large_whiteout_x, large_whiteout_y, large_whiteout_width, large_whiteout_height, fill=1, stroke=1)

            # Light gray color for the whiteout
            light_gray = (0.95, 0.95, 0.95)  # RGB values for a light gray

            # Variables for the light gray whiteout
            nettopris_text_x = 465
            nettopris_text_y = 440 + move_down

            # Compute the dimensions of the text (approximated for now, adjust as needed)
            text_width = 80  # this is an approximation; adjust based on your actual text width
            text_height = 20  # this is an approximation; adjust based on your font size

            whiteout_nettopris_x = nettopris_text_x - 6
            whiteout_nettopris_y = nettopris_text_y - 5
            whiteout_nettopris_width = text_width + 10
            whiteout_nettopris_height = text_height

            # Draw the light gray whiteout
            can_sixth.setFillColor(light_gray)
            can_sixth.rect(whiteout_nettopris_x, whiteout_nettopris_y, whiteout_nettopris_width, whiteout_nettopris_height, fill=True, stroke=False)

            # Format the nettopris and write it over the whiteout
            formatted_nettopris = "SEK {:,.2f}".format(int(nettopris)).replace(",", " ").replace(".", ",")
            can_sixth.setFont(bold_font_name, 10)
            can_sixth.setFillColor(black)
            can_sixth.drawString(nettopris_text_x, nettopris_text_y, formatted_nettopris)

            if laddbox_selected == "Ja":
                note_x = 35
                note_y = 614 + move_down
                note = f"1 x CM10 CheckWatt-installation"
            else:
                note_x = 35
                note_y = 624 + move_down
                note = f"1 x CM10 CheckWatt-installation"

            can_sixth.setFont(font_name, 9)
            can_sixth.drawString(note_x, note_y, note)

            can_sixth.save()
            packet_sixth.seek(0)
            new_pdf_7th = PdfReader(packet_sixth)
            page.merge_page(new_pdf_7th.pages[0])

        writer.add_page(page)

        # Add pages from the additional PDF after the third page
        if page_num == insert_position - 2:
            for i in range(len(additional_pdf.pages)):
                writer.add_page(additional_pdf.pages[i])

        if page_num == 2:  # Assuming the graph is on the 3rd page, index is 0-based
            anvandare_file = open("files/användare.pdf", "rb")
            anvandare_pdf = PdfReader(anvandare_file)
            for i in range(len(anvandare_pdf.pages)):
                writer.add_page(anvandare_pdf.pages[i])

        # Add the page from orderflow.pdf after the 5th page
        if page_num == 3:  # 5th page, index is 0-based
            writer.add_page(orderflow_pdf.pages[0])

    # Create a PDF in memory with the image
    packet_endpage = io.BytesIO()
    can_endpage = canvas.Canvas(packet_endpage, pagesize=A4)
    img_endpage = Image("files/endpage.png")
    img_endpage.drawHeight = A4[1]  # Set height to A4 height
    img_endpage.drawWidth = A4[0]  # Set width to A4 width
    img_endpage.drawOn(can_endpage, 0, 0)  # Set x, y coordinates to the bottom-left corner
    can_endpage.save()

    packet_endpage.seek(0)
    new_pdf_endpage = PdfReader(packet_endpage)

    # Create a new PdfWriter object
    new_writer = PdfWriter()

    # Iterate through existing pages and add them to new_writer
    for i, page in enumerate(writer.pages):
        if i == len(writer.pages) - 1:  # If it's the last page
            # Merge the new PDF (from endpage.png) onto the last page
            page.merge_page(new_pdf_endpage.pages[0])
            
        # Add (or re-add) the page to the new PdfWriter object
        new_writer.add_page(page)

    # Write the final PDF to file
    with open(output_path, "wb") as f_out:
        new_writer.write(f_out)

    # Close all opened files
    f_in.close()
    add_file.close()
    orderflow_file.close()
