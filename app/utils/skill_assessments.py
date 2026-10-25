"""Branch-relevant skill assessment bank + sync helper."""
from __future__ import annotations

import json

from app.extensions import db
from app.models import AptitudeResult, AptitudeTest

CSE = "Computer Science & Engineering"
ECE = "Electronics & Communication Engineering"
EEE = "Electrical & Electronics Engineering"
MECH = "Mechanical Engineering"
CIVIL = "Civil Engineering"
ALL = "All Branches"


def _q(question, options, answer, explanation=""):
    item = {"question": question, "options": options, "answer": answer}
    if not explanation and isinstance(answer, int) and 0 <= answer < len(options):
        explanation = f"The correct answer is: {options[answer]}."
    if explanation:
        item["explanation"] = explanation
    return item


SKILL_ASSESSMENTS = [
    # ---- Shared soft skill ----
    {
        "title": "Professional Communication Skills",
        "category": "Soft Skills",
        "branches": ALL,
        "duration_minutes": 8,
        "questions": [
            _q("In a formal email to a recruiter, which greeting is most appropriate?",
               ["Hey!", "Dear Sir/Madam,", "Yo,", "Hiya"], 1,
               "Formal openings like 'Dear Sir/Madam' or 'Dear Hiring Manager' are standard for recruiters."),
            _q("Which behaviour best shows active listening in an interview?",
               ["Interrupting frequently", "Paraphrasing what the interviewer said", "Checking your phone", "Staying silent throughout"], 1,
               "Paraphrasing confirms understanding and shows engagement."),
            _q("Best way to handle a question you cannot answer in an interview?",
               ["Invent an answer confidently", "Admit the gap and outline how you would find out", "Stay silent", "Change the topic"], 1,
               "Honesty plus a learning plan is valued more than guessing."),
            _q("Good practice while presenting a project to a panel?",
               ["Reading slides word-for-word", "Making eye contact and explaining in your own words", "Speaking very fast to save time", "Avoiding questions"], 1),
            _q("Which closing is most professional for a thank-you email after an interview?",
               ["Thanks, bye", "Best regards,", "Later!", "Sent from my phone"], 1),
        ],
    },
    # ---- CSE ----
    {
        "title": "Python Programming",
        "category": "Python",
        "branches": CSE,
        "duration_minutes": 12,
        "questions": [
            _q("What is the output of: print(type([]))?",
               ["<class 'list'>", "<class 'array'>", "<class 'tuple'>", "<class 'dict'>"], 0),
            _q("Which keyword defines a function in Python?",
               ["func", "def", "function", "lambda"], 1,
               "`def` creates a named function; `lambda` creates an anonymous expression."),
            _q("What does len('RGUKT') return?", ["4", "5", "6", "Error"], 1),
            _q("Which structure stores key-value pairs?",
               ["List", "Tuple", "Set", "Dictionary"], 3),
            _q("Correct file extension for Python files?",
               [".pt", ".py", ".pyt", ".pyth"], 1),
            _q("Which construct is used for exception handling?",
               ["try/except", "catch/throw", "error/handle", "if/else"], 0),
        ],
    },
    {
        "title": "SQL & Databases",
        "category": "SQL",
        "branches": CSE,
        "duration_minutes": 10,
        "questions": [
            _q("Which SQL clause filters rows?", ["ORDER BY", "WHERE", "GROUP BY", "HAVING"], 1),
            _q("Which command removes a table completely?", ["DELETE", "REMOVE", "DROP", "TRUNCATE TABLE"], 2,
               "DROP removes the table definition; DELETE removes rows."),
            _q("What does JOIN primarily do?",
               ["Deletes rows", "Combines rows from two or more tables", "Sorts a table", "Creates a table"], 1),
            _q("Which keyword returns only distinct values?",
               ["UNIQUE", "DISTINCT", "ONLY", "SINGLE"], 1),
            _q("Which clause groups rows for aggregates?",
               ["WHERE", "ORDER BY", "GROUP BY", "FILTER"], 2),
        ],
    },
    {
        "title": "Web Development Basics",
        "category": "Web Dev",
        "branches": CSE,
        "duration_minutes": 10,
        "questions": [
            _q("Which HTML tag links an external CSS file?",
               ["<style>", "<link>", "<css>", "<script>"], 1),
            _q("Which CSS property controls text size?",
               ["text-style", "font-size", "text-size", "font-style"], 1),
            _q("Which JS method adds an element to the end of an array?",
               ["push()", "pop()", "shift()", "unshift()"], 0),
            _q("What does fetch() primarily do in JavaScript?",
               ["Style elements", "Make network/HTTP requests", "Define variables", "Loop over arrays"], 1),
            _q("Which CSS layout model is commonly used for responsive grids?",
               ["Flexbox/Grid", "Table only", "Float only", "Inline only"], 0),
        ],
    },
    {
        "title": "Data Structures & Algorithms",
        "category": "DSA",
        "branches": CSE,
        "duration_minutes": 10,
        "questions": [
            _q("Time complexity of binary search on a sorted array?",
               ["O(n)", "O(log n)", "O(n^2)", "O(1)"], 1),
            _q("Which structure uses LIFO order?",
               ["Queue", "Stack", "Array", "Linked List"], 1),
            _q("Which sort has the best average-case complexity among these?",
               ["Bubble Sort", "Selection Sort", "Merge Sort", "Insertion Sort"], 2,
               "Merge sort averages O(n log n)."),
            _q("In a singly linked list, each node's pointer refers to:",
               ["The previous node", "The next node", "The head node", "The tail node"], 1),
            _q("Ideal structure for BFS traversal?",
               ["Stack", "Queue", "Heap", "Trie"], 1),
        ],
    },
    {
        "title": "Object-Oriented Programming (CSE)",
        "category": "OOP",
        "branches": CSE,
        "duration_minutes": 10,
        "questions": [
            _q("Which OOP principle hides internal details and exposes only necessary interfaces?",
               ["Inheritance", "Encapsulation", "Polymorphism", "Compilation"], 1),
            _q("Method overloading is an example of:",
               ["Compile-time polymorphism", "Runtime polymorphism", "Encapsulation", "Abstraction only"], 0),
            _q("A class that cannot be instantiated and may contain abstract methods is called:",
               ["Final class", "Abstract class", "Static class", "Inner class"], 1),
            _q("Which keyword in Java prevents a class from being subclassed?",
               ["static", "final", "private", "volatile"], 1),
            _q("Inheritance primarily promotes:",
               ["Code reuse", "Slower execution always", "Database storage", "Network I/O"], 0),
        ],
    },
    # ---- ECE ----
    {
        "title": "Digital Electronics Fundamentals",
        "category": "Digital Electronics",
        "branches": ECE,
        "duration_minutes": 12,
        "questions": [
            _q("The binary equivalent of decimal 13 is:",
               ["1101", "1011", "1110", "1001"], 0),
            _q("A full adder has how many inputs?",
               ["2", "3", "4", "1"], 1,
               "Two operand bits plus carry-in."),
            _q("Which gate outputs 1 only when all inputs are 1?",
               ["OR", "NAND", "AND", "XOR"], 2),
            _q("A flip-flop is primarily used as a:",
               ["Combinational circuit", "Memory / sequential element", "Amplifier", "Filter"], 1),
            _q("In 2's complement, −1 in 4 bits is represented as:",
               ["0001", "1001", "1111", "0111"], 2),
            _q("Multiplexer selects one of many inputs based on:",
               ["Clock only", "Select lines", "Reset pin", "Power supply"], 1),
        ],
    },
    {
        "title": "Signals, Systems & Communication",
        "category": "Communication",
        "branches": ECE,
        "duration_minutes": 12,
        "questions": [
            _q("Nyquist sampling theorem states sampling frequency must be:",
               ["Less than max signal frequency", "At least twice the highest frequency", "Equal to signal amplitude", "Independent of bandwidth"], 1),
            _q("AM stands for:",
               ["Amplitude Modulation", "Angular Modulation", "Analog Multiplexing", "Average Magnitude"], 0),
            _q("Fourier transform converts a signal from:",
               ["Frequency to time only", "Time domain to frequency domain", "Digital to analog", "Noise to signal"], 1),
            _q("Which modulation is more noise-immune for the same SNR typically?",
               ["AM", "FM", "Baseband only", "OOK always"], 1),
            _q("A low-pass filter ideally:",
               ["Passes high frequencies", "Passes low frequencies", "Blocks DC only", "Amplifies noise"], 1),
        ],
    },
    {
        "title": "Microcontrollers & Embedded Systems",
        "category": "Embedded",
        "branches": f"{ECE}, {EEE}",
        "duration_minutes": 10,
        "questions": [
            _q("An microcontroller typically integrates CPU with:",
               ["Only RAM", "Memory and peripherals on-chip", "Only GPU", "External OS only"], 1),
            _q("GPIO pins are used to:",
               ["Generate RF only", "Read/write digital I/O", "Store programs permanently", "Replace crystal oscillators"], 1),
            _q("Which memory typically stores firmware that persists after power-off?",
               ["SRAM", "Flash / ROM", "Cache only", "Register file"], 1),
            _q("An interrupt allows the CPU to:",
               ["Ignore all I/O forever", "Respond to events asynchronously", "Disable the clock", "Delete memory"], 1),
            _q("UART is commonly used for:",
               ["Wireless Wi-Fi only", "Serial communication", "Image compression", "Power regulation"], 1),
        ],
    },
    {
        "title": "VLSI & Semiconductor Basics",
        "category": "VLSI",
        "branches": ECE,
        "duration_minutes": 10,
        "questions": [
            _q("CMOS technology uses complementary:",
               ["BJTs only", "NMOS and PMOS transistors", "Diodes only", "Vacuum tubes"], 1),
            _q("Moore's law historically observed roughly:",
               ["Constant transistor counts", "Doubling of transistors on a chip over time", "Halving of clock speed yearly", "Zero power consumption"], 1),
            _q("In digital VLSI, static power is mainly due to:",
               ["Leakage currents", "Only switching capacitance", "Antenna effects only", "PCB traces"], 0),
            _q("ASIC stands for:",
               ["Analog Signal Integrated Circuit", "Application-Specific Integrated Circuit", "Automatic System Interface Chip", "Array Sequential IC"], 1),
            _q("Which is a standard HDL used for digital design?",
               ["HTML", "Verilog / VHDL", "CSS", "SQL"], 1),
        ],
    },
    # ---- EEE ----
    {
        "title": "Electrical Circuits & Machines",
        "category": "Circuits",
        "branches": EEE,
        "duration_minutes": 12,
        "questions": [
            _q("Ohm's law states V =",
               ["I/R", "IR", "I+R", "R/I"], 1),
            _q("In a series circuit, current is:",
               ["Different in each resistor", "Same through all elements", "Always zero", "Proportional only to voltage source type"], 1),
            _q("A transformer primarily works on the principle of:",
               ["Electrostatics", "Mutual induction", "Photoelectric effect", "Hall effect"], 1),
            _q("Unit of electrical power is:",
               ["Joule", "Watt", "Coulomb", "Ohm"], 1),
            _q("Synchronous speed of an induction motor depends on:",
               ["Supply frequency and number of poles", "Only rotor resistance", "Only load torque", "Only stator resistance"], 0),
            _q("Kirchhoff's Current Law (KCL) states that at a node:",
               ["Voltages sum to zero", "Algebraic sum of currents is zero", "Power is infinite", "Resistance is constant"], 1),
        ],
    },
    {
        "title": "Power Systems Fundamentals",
        "category": "Power Systems",
        "branches": EEE,
        "duration_minutes": 10,
        "questions": [
            _q("Typical transmission voltages are preferred high because:",
               ["It increases I²R losses", "It reduces current and thus line losses for given power", "It eliminates transformers", "It removes need for insulation"], 1),
            _q("A circuit breaker is used to:",
               ["Only measure voltage", "Interrupt fault currents safely", "Step up voltage only", "Store energy"], 1),
            _q("Power factor is:",
               ["Real power / apparent power", "Reactive power only", "Voltage × current always", "Frequency ÷ voltage"], 0),
            _q("Which device steps voltage up or down in AC systems?",
               ["Rectifier", "Transformer", "Inverter only", "Battery"], 1),
            _q("Three-phase power systems are preferred because they:",
               ["Cannot transmit power", "Offer constant power transfer and efficient generation", "Need no conductors", "Work only on DC"], 1),
        ],
    },
    {
        "title": "Control Systems & Power Electronics",
        "category": "Control & PE",
        "branches": EEE,
        "duration_minutes": 10,
        "questions": [
            _q("A closed-loop control system uses:",
               ["No sensors", "Feedback to correct error", "Open wires only", "Only manual switches"], 1),
            _q("A thyristor (SCR) is commonly used for:",
               ["Optical fiber", "Controlled power switching", "Audio amplification only", "Data storage"], 1),
            _q("PWM in power electronics primarily helps to:",
               ["Control average output by duty cycle", "Increase resistance permanently", "Eliminate all harmonics always", "Convert AC to light"], 0),
            _q("Stability of a control system often analyzed using:",
               ["Bode / Nyquist / root locus methods", "Only Ohm's law", "SQL queries", "HTML parsers"], 0),
            _q("An inverter converts:",
               ["DC to AC", "AC to DC", "Heat to light", "Voltage to resistance"], 0),
        ],
    },
    # ---- Mechanical ----
    {
        "title": "Engineering Mechanics & SOM",
        "category": "Mechanics",
        "branches": MECH,
        "duration_minutes": 12,
        "questions": [
            _q("Stress is defined as:",
               ["Force × area", "Force / area", "Area / force", "Mass × acceleration only"], 1),
            _q("Young's modulus is the ratio of:",
               ["Shear stress to shear strain", "Longitudinal stress to longitudinal strain (within elastic limit)", "Volume stress to volume strain", "Force to mass"], 1),
            _q("A simply supported beam with central point load has max bending moment at:",
               ["Supports", "Mid-span", "Everywhere equal", "Beyond supports"], 1),
            _q("Poisson's ratio relates:",
               ["Lateral strain to longitudinal strain", "Force to torque", "Pressure to temperature", "Speed to acceleration"], 0),
            _q("SI unit of moment of inertia (mass) is:",
               ["kg·m²", "N·m", "Pa", "Joule"], 0),
            _q("Hooke's law is valid within:",
               ["Plastic range only", "Elastic limit / proportional limit", "Fracture region", "Creep region only"], 1),
        ],
    },
    {
        "title": "Thermodynamics & Heat Transfer",
        "category": "Thermal",
        "branches": MECH,
        "duration_minutes": 10,
        "questions": [
            _q("First law of thermodynamics is essentially conservation of:",
               ["Momentum", "Energy", "Mass only", "Entropy"], 1),
            _q("An adiabatic process has:",
               ["Constant pressure", "No heat transfer (Q=0)", "Constant volume only", "Infinite heat transfer"], 1),
            _q("Heat transfer by electromagnetic waves is called:",
               ["Conduction", "Convection", "Radiation", "Diffusion"], 2),
            _q("Carnot cycle efficiency depends on:",
               ["Working fluid only", "Source and sink temperatures", "Piston color", "Ambient humidity only"], 1),
            _q("SI unit of heat is:",
               ["Watt", "Joule", "Pascal", "Newton"], 1),
        ],
    },
    {
        "title": "Manufacturing & Machine Design",
        "category": "Manufacturing",
        "branches": MECH,
        "duration_minutes": 10,
        "questions": [
            _q("CNC stands for:",
               ["Computer Numerical Control", "Central Network Circuit", "Control Node Chip", "Cyclic Neutral Coupling"], 0),
            _q("Which process joins metals by melting with a filler typically?",
               ["Turning", "Welding", "Milling only", "Drilling"], 1),
            _q("Factor of safety is:",
               ["Working stress / ultimate stress", "Ultimate (or yield) capacity / working load", "Always equal to 1", "Density / stress"], 1),
            _q("CAD is primarily used for:",
               ["Design drafting and modeling", "Only machining chips", "Payroll", "Chemical reactions"], 0),
            _q("Annealing of steel generally:",
               ["Hardens and embrittles always", "Softens and relieves stresses", "Removes all carbon", "Converts to rubber"], 1),
        ],
    },
    {
        "title": "Fluid Mechanics Basics",
        "category": "Fluids",
        "branches": f"{MECH}, {CIVIL}",
        "duration_minutes": 10,
        "questions": [
            _q("Pascal's law relates to:",
               ["Pressure transmission in confined fluids", "Ideal gas temperature only", "Magnetic fields", "Sound speed in solids"], 0),
            _q("Bernoulli's equation assumes flow that is typically:",
               ["Compressible and viscous always", "Steady, incompressible, inviscid along a streamline", "Only turbulent", "Only multiphase"], 1),
            _q("Reynolds number helps predict:",
               ["Laminar vs turbulent flow", "Only density", "Only color of fluid", "Electrical conductivity"], 0),
            _q("Viscosity is a measure of:",
               ["Fluid's resistance to shear / flow", "Only temperature", "Only pressure", "Only mass"], 0),
            _q("Continuity equation for incompressible flow states:",
               ["A1V1 = A2V2", "P = ρgh only", "F = ma only", "V = IR"], 0),
        ],
    },
    # ---- Civil ----
    {
        "title": "Structural Analysis Basics",
        "category": "Structures",
        "branches": CIVIL,
        "duration_minutes": 12,
        "questions": [
            _q("A statically determinate structure can be analyzed using:",
               ["Only FEM software", "Equilibrium equations alone", "Only dynamics", "Only soil reports"], 1),
            _q("Bending moment diagram for a simply supported beam with UDL is typically:",
               ["Triangular", "Parabolic", "Rectangular constant", "Zero everywhere"], 1),
            _q("Shear force is maximum typically near:",
               ["Supports for simple beams with gravity loads", "Always midspan only", "Never at supports", "Atmosphere"], 0),
            _q("A cantilever beam is fixed at:",
               ["Both ends", "One end", "Neither end", "Midpoint only"], 1),
            _q("Influence lines are used to study effect of:",
               ["Moving loads", "Only temperature", "Only humidity", "Paint color"], 0),
            _q("Euler's buckling load increases when:",
               ["Length increases", "Flexural rigidity EI increases / effective length decreases", "Slenderness increases only", "Load eccentricity ignored always"], 1),
        ],
    },
    {
        "title": "Concrete Technology & Materials",
        "category": "Concrete",
        "branches": CIVIL,
        "duration_minutes": 10,
        "questions": [
            _q("OPC stands for:",
               ["Ordinary Portland Cement", "Organic Polymer Concrete", "Open Precast Column", "Oxide Pressure Cement"], 0),
            _q("Water-cement ratio primarily affects concrete:",
               ["Color only", "Strength and workability", "Only setting time of steel", "Reinforcement grade"], 1),
            _q("Curing of concrete is done to:",
               ["Dry it instantly", "Maintain moisture for hydration", "Remove cement", "Increase air voids intentionally"], 1),
            _q("M20 grade concrete roughly indicates characteristic strength of:",
               ["20 MPa", "200 MPa", "2 MPa", "20 Pa"], 0),
            _q("Aggregate in concrete mainly provides:",
               ["Only color", "Bulk and strength economy", "Only workability chemicals", "Steel bonding via magnetism"], 1),
        ],
    },
    {
        "title": "Surveying & Geotechnical Basics",
        "category": "Survey & Geotech",
        "branches": CIVIL,
        "duration_minutes": 10,
        "questions": [
            _q("A theodolite is primarily used to measure:",
               ["Only distances by tape", "Horizontal and vertical angles", "Concrete slump", "Steel hardness"], 1),
            _q("Bearing capacity of soil refers to:",
               ["Maximum load soil can support safely", "Only moisture content", "Only color of soil", "Wind speed"], 0),
            _q("Contour lines join points of equal:",
               ["Temperature", "Elevation", "Pressure only", "Population"], 1),
            _q("SPT in geotech stands for:",
               ["Standard Penetration Test", "Soil Pressure Tool", "Surface Painting Test", "Seismic Peak Time"], 0),
            _q("Compaction of soil aims to:",
               ["Increase voids intentionally", "Increase density and strength by reducing air voids", "Add water indefinitely", "Remove all solids"], 1),
        ],
    },
    {
        "title": "Transportation & Environmental Engg",
        "category": "Transportation",
        "branches": CIVIL,
        "duration_minutes": 10,
        "questions": [
            _q("IRC is associated with standards for:",
               ["Indian Roads Congress (highway design)", "International Radio Code", "Iron Reinforcement Certificate", "Indoor Roofing Code"], 0),
            _q("Camber on a road is provided to:",
               ["Increase accidents", "Drain surface water", "Reduce sight distance always", "Eliminate shoulders"], 1),
            _q("BOD in water quality stands for:",
               ["Biological Oxygen Demand", "Basic Organic Density", "Binary Output Data", "Bonded Oxide Deposit"], 0),
            _q("A septic tank is used for:",
               ["Primary treatment of domestic sewage", "High-voltage transmission", "Soil compaction", "Bitumen mixing only"], 0),
            _q("Sight distance in highway design ensures:",
               ["Driver can stop or overtake safely", "Only aesthetic curves", "Maximum noise", "Zero traffic always"], 0),
        ],
    },
    # ---- Extra CSE ----
    {
        "title": "Operating Systems",
        "category": "OS",
        "branches": CSE,
        "duration_minutes": 10,
        "questions": [
            _q("A process in the ready state is waiting for:",
               ["I/O completion only", "CPU allocation", "Compilation", "Disk formatting"], 1,
               "Ready means the process is eligible to run and waiting for the scheduler to assign a CPU."),
            _q("Which scheduling algorithm can cause starvation of low-priority processes?",
               ["Round Robin", "FCFS", "Priority scheduling (without aging)", "FIFO I/O only"], 2),
            _q("A deadlock requires four conditions including:",
               ["Mutual exclusion, hold and wait, no preemption, circular wait", "Paging only", "Cache misses only", "User-mode traps only"], 0),
            _q("Virtual memory typically uses:",
               ["Only registers", "Paging and/or segmentation", "Only magnetic tape", "Only BIOS"], 1),
            _q("A semaphore is mainly used for:",
               ["Process synchronization / mutual exclusion", "Compiling C code", "Drawing UI", "DNS lookup"], 0),
        ],
    },
    {
        "title": "Computer Networks",
        "category": "Networks",
        "branches": CSE,
        "duration_minutes": 10,
        "questions": [
            _q("TCP operates at which OSI layer?",
               ["Physical", "Network", "Transport", "Application"], 2),
            _q("IP address 192.168.1.1 is typically:",
               ["A public unicast on the internet backbone", "A private (RFC1918) address", "A multicast address", "An IPv6 address"], 1),
            _q("DNS primarily maps:",
               ["MAC to IP only", "Domain names to IP addresses", "Ports to processes on the NIC", "Files to inodes"], 1),
            _q("HTTPS commonly uses which port?",
               ["21", "25", "80", "443"], 3),
            _q("A switch in a LAN typically forwards frames based on:",
               ["IP addresses only", "MAC addresses", "URLs", "Process IDs"], 1),
        ],
    },
    {
        "title": "Core Java & JVM Basics",
        "category": "Java",
        "branches": CSE,
        "duration_minutes": 10,
        "questions": [
            _q("Which keyword prevents a Java method from being overridden?",
               ["static", "final", "volatile", "transient"], 1),
            _q("The JVM is responsible for:",
               ["Only compiling .java to .class", "Executing bytecode and providing runtime services", "Replacing the OS kernel", "Drawing CSS"], 1),
            _q("Which collection does not allow duplicate elements?",
               ["List", "Set", "ArrayList only", "LinkedList only"], 1),
            _q("Checked exceptions in Java must be:",
               ["Ignored always", "Handled with try/catch or declared with throws", "Thrown only by the JVM", "Used only in interfaces"], 1),
            _q("String in Java is:",
               ["A primitive type", "An immutable class", "A mutable array of chars always exposed", "A keyword for numbers"], 1),
        ],
    },
    # ---- Extra ECE ----
    {
        "title": "Analog Electronics",
        "category": "Analog",
        "branches": ECE,
        "duration_minutes": 10,
        "questions": [
            _q("An ideal op-amp has:",
               ["Zero open-loop gain", "Infinite open-loop gain and infinite input impedance (ideal model)", "Zero bandwidth always", "No feedback possible"], 1),
            _q("A diode in forward bias typically:",
               ["Blocks current", "Conducts current after cut-in voltage", "Acts as an inductor", "Stores magnetic flux"], 1),
            _q("BJT operating in saturation is used mainly as:",
               ["A linear amplifier always", "A closed switch (ON)", "An open switch (OFF)", "A crystal oscillator only"], 1),
            _q("A bypass capacitor on an emitter resistor is used to:",
               ["Increase AC gain by grounding emitter for AC", "Remove DC supply", "Create oscillations always", "Rectify the signal"], 0),
            _q("The 555 timer IC is commonly used for:",
               ["Only Ethernet PHY", "Astable/monostable timing circuits", "FPGA synthesis", "SQL queries"], 1),
        ],
    },
    # ---- Extra EEE ----
    {
        "title": "Electrical Measurements & Protection",
        "category": "Measurements",
        "branches": EEE,
        "duration_minutes": 10,
        "questions": [
            _q("A CT (current transformer) is used to:",
               ["Measure/scale high currents safely for meters and relays", "Step up current for motors always", "Store energy", "Generate harmonics"], 0),
            _q("A wattmeter typically measures:",
               ["Only voltage", "Active (real) power", "Only frequency", "Only resistance"], 1),
            _q("Overcurrent protection operates when:",
               ["Current exceeds a set threshold for a defined time", "Voltage is exactly 230 V", "Power factor is unity", "Load is capacitive only"], 0),
            _q("An earth leakage / residual current device trips on:",
               ["Difference between live and neutral currents", "Only high voltage", "Only temperature", "Only frequency drift"], 0),
            _q("Accuracy class of an instrument indicates:",
               ["Color of the scale", "Maximum permissible error as a percentage", "Only the price", "Only the weight"], 1),
        ],
    },
    # ---- Extra Mechanical ----
    {
        "title": "Theory of Machines & Design",
        "category": "TOM",
        "branches": MECH,
        "duration_minutes": 10,
        "questions": [
            _q("A kinematic pair is:",
               ["Two links joined so that relative motion is possible", "A thermodynamic cycle", "A welding joint only", "A fluid particle"], 0),
            _q("Degrees of freedom of a planar mechanism with n links and j joints (Gruebler's, typical) is:",
               ["3(n−1) − 2j", "n + j", "Always 1", "2n − j"], 0),
            _q("A flywheel is used to:",
               ["Store rotational energy and smooth speed fluctuations", "Increase friction always", "Cool the engine only", "Measure strain"], 0),
            _q("In a four-bar linkage, the crank is the link that:",
               ["Cannot rotate fully", "Can make a complete revolution", "Is always the coupler", "Is the fixed frame"], 1),
            _q("Gear ratio of a simple gear train is:",
               ["Driven teeth / driving teeth (speed inverse to teeth)", "Always 1", "Independent of teeth", "Equal to module only"], 0),
        ],
    },
    # ---- Extra Civil ----
    {
        "title": "Hydraulics & Water Resources",
        "category": "Hydraulics",
        "branches": CIVIL,
        "duration_minutes": 10,
        "questions": [
            _q("Discharge over a rectangular weir is proportional to:",
               ["H^(3/2) (head to the power 1.5, theoretically)", "H only", "H^5", "Independent of head"], 0),
            _q("Darcy-Weisbach equation is used for:",
               ["Head loss due to friction in pipes", "Bending of beams", "Concrete mix design", "Traffic volume"], 0),
            _q("A confined aquifer is bounded by:",
               ["Impermeable layers above and below", "Only the atmosphere", "Only rivers", "Steel plates"], 0),
            _q("Manning's formula estimates:",
               ["Open-channel flow velocity", "Steel yield stress", "Soil cohesion only", "Bitumen viscosity only"], 0),
            _q("Rapid sand filters in water treatment mainly remove:",
               ["Suspended matter after coagulation/sedimentation", "All dissolved salts always", "Only viruses with UV", "Hardness exclusively"], 0),
        ],
    },
    {
        "title": "Campus HR Interview Prep",
        "category": "Soft Skills",
        "branches": ALL,
        "duration_minutes": 8,
        "questions": [
            _q("STAR method in interviews stands for:",
               ["Start, Talk, Argue, Run", "Situation, Task, Action, Result", "Study, Test, Apply, Repeat", "Skill, Talent, Award, Rank"], 1),
            _q("Best way to discuss a project you built in a team?",
               ["Claim you did everything alone", "Explain your specific contributions and the team's outcome", "Blame teammates", "Skip technical details entirely"], 1),
            _q("If asked 'What is your weakness?', a strong pattern is:",
               ["Say you have none", "Name a real growth area and how you are improving it", "List every failure", "Criticize your college"], 1),
            _q("When salary is asked early and you are unsure, a safe approach is:",
               ["Demand an extreme number immediately", "Share a researched range and express flexibility for the role/learning", "Refuse to speak", "Ask them to match a friend"], 1),
            _q("Follow-up after an interview is best done:",
               ["With a short professional thank-you within a day", "By calling HR every hour", "Via memes on LinkedIn", "Never"], 0),
        ],
    },
]


def test_matches_branch(branches_field: str, student_branch: str) -> bool:
    if not branches_field or branches_field.strip() in ("", ALL, "All"):
        return True
    if branches_field.strip() == "__retired__":
        return False
    student = (student_branch or "").strip().lower()
    allowed = [b.strip().lower() for b in branches_field.split(",") if b.strip()]
    return student in allowed or any(student.startswith(a) or a.startswith(student) for a in allowed)


def sync_skill_assessments():
    """Upsert branch-mapped skill assessments (safe to run on every startup)."""
    existing = {
        t.title: t
        for t in AptitudeTest.query.filter_by(test_type="skill").all()
    }
    changed = False
    for spec in SKILL_ASSESSMENTS:
        payload = json.dumps(spec["questions"])
        row = existing.get(spec["title"])
        if row:
            if (
                row.category != spec["category"]
                or row.duration_minutes != spec["duration_minutes"]
                or (row.branches or "") != spec["branches"]
                or row.questions_json != payload
            ):
                row.category = spec["category"]
                row.duration_minutes = spec["duration_minutes"]
                row.branches = spec["branches"]
                row.questions_json = payload
                changed = True
        else:
            db.session.add(
                AptitudeTest(
                    title=spec["title"],
                    category=spec["category"],
                    test_type="skill",
                    duration_minutes=spec["duration_minutes"],
                    branches=spec["branches"],
                    questions_json=payload,
                )
            )
            changed = True

    # Retire obsolete generic titles that were superseded / remapped
    obsolete = {
        "Communication Skills",
        "Java Programming",
        "C Programming",
        "General Technical Skills",
    }
    for title in obsolete:
        row = existing.get(title)
        if row:
            has_results = AptitudeResult.query.filter_by(test_id=row.id).first()
            if has_results:
                row.branches = "__retired__"
            else:
                db.session.delete(row)
            changed = True

    if changed:
        db.session.commit()