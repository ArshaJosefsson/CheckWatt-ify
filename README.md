**CheckWatt-ify - PC ONLY - Supplementary Quotation Tool for OpenSolar (Fall Term 2023)**

Grid balancing services are essential in modern energy systems, ensuring that the supply and demand of electricity on the grid are consistently in equilibrium. CheckWatt's software aggregates the energy resources of multiple users, creating a virtual power plant that can provide these critical balancing services to the grid.

OpenSolar is a free and widely used quoting tool that we initially found valuable as a startup, primarily due to its intuitive and efficient design features. These features allow for the calculation of the yearly production value of solar panels, taking into account factors such as solar hours, roof incline, cardinal direction, and more.

However, OpenSolar had significant limitations at the time of our product offering. Specifically, it did not provide an easy or integrated way to calculate ROI related to the revenue generated by batteries through CheckWatt. Additionally, the platform was not equipped to accurately calculate Swedish subsidies for private battery and solar installations. Furthermore, updating prices within OpenSolar was a cumbersome process.

To address these challenges, I developed CheckWatt-ify with the help of Chat GPT 4, a pdf manipulating tool using PyPDF2/Reportlab that enables salespeople to generate quotes with accurately calculated and graphically represented ROI, incorporating the correct price and subsidy amounts. The values of all factors are gathered from an excel file using Pandas/NumPy. We also used CheckWatt-ify to improve the quality of images and PDFs in our quotations, as we were not satisfied with the quality provided by the OpenSolar platform.


**IMPORTANT FOR USE - How To**
------------------------------
Download main.py, pdf_generator.py and files and have them in the same directory.
Some computers have to temporarily disable Microsoft Defender Antivirus to able to create this application.

Create .exe with PyInstaller through Terminal:
- "pip install pyinstaller"
- "cd "path_to_your_project_directory"
- "pyinstaller --onefile --windowed --icon=solarchoice.ico main.py"

Some computers have to add CheckWatt-ify as an exception to their Microsoft Defender Antivirus to able to execute the application.

(Original OpenSolar design-quote is created and named Raw Quote.pdf)
1. Open CheckWatt-ify
2. Write in your preferred values. Note that "Kunduppgifter" doesn't function in this version.
3. "Besparing Open Solar" should be 12125 as in the raw quote. This adds the revenue from the energy produced by the solar panels to the battery installation.
4. Press "CheckWatt-ify"
5. Double click on raw quote.
6. Write a name for the new finalized quote.
7. Done!


Hidden Button
-------------
At the bottom of the GUI, there is a hidden button that allows users to search for an address and retrieve an image of the property from Google Maps via their API. This feature was envisioned as the first step toward developing our own design tool and ultimately integrating the entire quoting process internally, eliminating the need for reliance on OpenSolar or any other external service.


Comment
-------------
This program is currently in its initial form and was specifically developed to meet the quotation requirements for Solar Choice at the time of its creation. As such, it lacks the flexibility and adaptability needed to accommodate the diverse needs of different organizations.
