// Aircraft dossiers and per-part data for the viewer. Geometry lives in ./assets/models/<id>.glb
// (built in Blender by ../blender/<id>.py); each GLB has one node part_<key> per entry in `parts`.
export const AIRCRAFT = [
  {
    "id": "blackhawk",
    "tab": "UH-60 BLACK HAWK",
    "file": "./assets/models/blackhawk.glb",
    "info": {
      "name": "UH-60 Black Hawk",
      "variant": "Sikorsky · Utility Tactical Transport",
      "role": "Utility / Assault",
      "origin": "United States",
      "year": "In service 1979",
      "desc": "A four-blade, twin-engine medium utility helicopter — the US Army's tactical transport workhorse. It carries an 11-troop squad, casualties or slung cargo, and flies assault, medevac, special-operations and VIP missions worldwide.",
      "specs": [
        [
          "Crew",
          "2 + 11 troops"
        ],
        [
          "Length",
          "19.76 m"
        ],
        [
          "Rotor",
          "16.36 m · 4-blade"
        ],
        [
          "Max speed",
          "294 km/h"
        ],
        [
          "Engines",
          "2 × GE T700"
        ],
        [
          "Introduced",
          "1979"
        ]
      ]
    },
    "parts": {
      "fuselage": {
        "name": "Fuselage",
        "role": "Primary airframe",
        "fn": "The crashworthy aluminium-and-composite airframe carries the cockpit, 11-troop cabin, engines, fuel and rotor loads. A wide sliding door each side loads troops and cargo fast.",
        "mats": [
          "Aluminium-alloy frames",
          "Composite skin",
          "Kevlar armour floor",
          "Self-sealing tanks"
        ],
        "specs": [
          [
            "Cabin",
            "11 troops"
          ],
          [
            "Length",
            "19.76 m"
          ],
          [
            "Width",
            "2.36 m"
          ],
          [
            "Doors",
            "2 × sliding"
          ]
        ]
      },
      "cockpit": {
        "name": "Cockpit & Cabin",
        "role": "Crew · troop station",
        "fn": "Side-by-side pilots fly behind an armoured wrap-around windscreen with a glass-cockpit instrument display. Behind them the cabin seats a full infantry squad with wide sliding doors and gunner windows.",
        "mats": [
          "Bullet-resistant windscreen",
          "Armoured crew seats",
          "Glass-cockpit displays"
        ],
        "specs": [
          [
            "Pilots",
            "2 side-by-side"
          ],
          [
            "Seating",
            "11 troops"
          ],
          [
            "Windows",
            "Gunner / cabin"
          ]
        ]
      },
      "sensor": {
        "name": "FLIR / Sensor Suite",
        "role": "Vision · targeting",
        "fn": "A nose-mounted forward-looking infra-red turret with thermal and low-light cameras lets the crew fly and find targets in total darkness, dust or smoke.",
        "mats": [
          "Germanium IR optics",
          "Gyro-stabilised gimbal",
          "Magnesium housing"
        ],
        "specs": [
          [
            "Sensors",
            "FLIR · LLTV"
          ],
          [
            "Use",
            "Night / brown-out"
          ],
          [
            "Stabilised",
            "Yes"
          ]
        ]
      },
      "engine": {
        "name": "Twin Turboshafts",
        "role": "Powerplant",
        "fn": "Two General Electric T700 turboshaft engines drive the rotors through a central gearbox. Infra-red-suppressing exhausts cool the hot gas to hide the aircraft from heat-seeking missiles.",
        "mats": [
          "Nickel super-alloy turbine",
          "Titanium compressor",
          "IR-suppressing cowl"
        ],
        "specs": [
          [
            "Engines",
            "2 × GE T700"
          ],
          [
            "Power",
            "≈2 × 1420 kW"
          ],
          [
            "Gearbox",
            "Central main"
          ]
        ]
      },
      "mainRotor": {
        "name": "Main Rotor",
        "role": "Lift · thrust · control",
        "fn": "Four wide-chord composite blades on a titanium hub generate all the lift and directional thrust. Swept blade tips cut noise and improve high-speed efficiency; the whole disc tilts to move the aircraft.",
        "mats": [
          "Titanium / graphite spar blades",
          "Titanium hub",
          "Elastomeric bearings"
        ],
        "specs": [
          [
            "Blades",
            "4"
          ],
          [
            "Diameter",
            "16.36 m"
          ],
          [
            "Tip",
            "Swept"
          ],
          [
            "RPM",
            "≈258"
          ]
        ]
      },
      "tailRotor": {
        "name": "Tail Rotor & Fin",
        "role": "Anti-torque · yaw",
        "fn": "A canted four-blade tail rotor cancels the main-rotor torque so the airframe does not spin, and gives the pilot yaw control. Its 20° tilt also adds a little lift at the tail.",
        "mats": [
          "Composite blades",
          "Cross-beam titanium hub",
          "Steel pitch links"
        ],
        "specs": [
          [
            "Blades",
            "4"
          ],
          [
            "Cant",
            "20°"
          ],
          [
            "Fin",
            "Load-bearing"
          ]
        ]
      },
      "stabilator": {
        "name": "Stabilator",
        "role": "Pitch stability",
        "fn": "A moving horizontal tailplane that the flight computer tilts automatically with speed, keeping the nose level and the ride stable through the whole flight envelope.",
        "mats": [
          "Composite skin",
          "Electric actuators"
        ],
        "specs": [
          [
            "Type",
            "Variable-incidence"
          ],
          [
            "Control",
            "Automatic"
          ],
          [
            "Span",
            "4.4 m"
          ]
        ]
      },
      "gear": {
        "name": "Landing Gear",
        "role": "Ground contact",
        "fn": "A fixed tricycle undercarriage with two forward main wheels and a tail wheel. Energy-absorbing struts soak up hard and crash landings to protect the crew.",
        "mats": [
          "High-strength steel struts",
          "Oleo-pneumatic dampers",
          "Rubber tyres"
        ],
        "specs": [
          [
            "Type",
            "Fixed tailwheel"
          ],
          [
            "Mains",
            "2 forward"
          ],
          [
            "Role",
            "Crashworthy"
          ]
        ]
      }
    }
  },
  {
    "id": "apache",
    "tab": "AH-64 APACHE",
    "file": "./assets/models/apache.glb",
    "info": {
      "name": "AH-64 Apache",
      "variant": "Boeing · Attack Helicopter",
      "role": "Attack / Anti-armour",
      "origin": "United States",
      "year": "In service 1986",
      "desc": "A twin-engine, four-blade attack helicopter built around a stepped tandem cockpit, a chin-mounted 30 mm cannon and stub wings of rockets and Hellfire missiles. Flown by a pilot and a co-pilot/gunner, it hunts armour and provides close air support day or night with its nose TADS/PNVS sensor suite.",
      "specs": [
        [
          "Crew",
          "2 tandem"
        ],
        [
          "Length",
          "17.73 m"
        ],
        [
          "Rotor",
          "14.63 m · 4-blade"
        ],
        [
          "Max speed",
          "293 km/h"
        ],
        [
          "Engines",
          "2 × GE T700"
        ],
        [
          "Main gun",
          "30 mm M230"
        ],
        [
          "Missiles",
          "AGM-114 Hellfire"
        ]
      ]
    },
    "parts": {
      "fuselage": {
        "name": "Fuselage",
        "role": "Primary airframe",
        "fn": "The narrow, flat-sided aluminium-and-composite airframe is built around armoured tandem crew bays and a central rotor mast. Its slim cross-section and boron armour panels let it absorb cannon hits while keeping a small head-on target for the enemy.",
        "mats": [
          "Aluminium-alloy frames",
          "Composite skin",
          "Boron carbide crew armour",
          "Crashworthy structure"
        ],
        "specs": [
          [
            "Length",
            "17.73 m"
          ],
          [
            "Height",
            "3.87 m"
          ],
          [
            "Fuselage width",
            "1.0 m"
          ],
          [
            "Empty",
            "5165 kg"
          ]
        ]
      },
      "cockpit": {
        "name": "Tandem Cockpit",
        "role": "Crew station",
        "fn": "Two crew sit in a stepped tandem layout — the co-pilot/gunner low in front and the pilot raised behind — so both see forward past each other. Flat, bullet-resistant canopy panels and kevlar seat tubs protect the crew from 23 mm fire.",
        "mats": [
          "Flat bullet-resistant glass",
          "Boron/kevlar seat armour",
          "Integrated helmet sight"
        ],
        "specs": [
          [
            "Crew",
            "2 tandem"
          ],
          [
            "Gunner",
            "Front · low"
          ],
          [
            "Pilot",
            "Rear · raised"
          ],
          [
            "Protection",
            "Dual-redundant"
          ]
        ]
      },
      "sensors": {
        "name": "TADS / PNVS Turrets",
        "role": "Targeting · night vision",
        "fn": "The nose carries two stacked gyro-stabilised turrets: the larger lower TADS (Target Acquisition and Designation Sight) with day TV, thermal imager and laser designator, and the smaller upper PNVS (Pilot Night Vision Sensor) that feeds the pilot a thermal image for flying in total darkness.",
        "mats": [
          "Germanium thermal optics",
          "Day-TV camera",
          "Laser designator/rangefinder",
          "Gyro-stabilised gimbals"
        ],
        "specs": [
          [
            "Lower",
            "TADS"
          ],
          [
            "Upper",
            "PNVS"
          ],
          [
            "Range",
            "Laser designation"
          ],
          [
            "Slaved",
            "Helmet sight"
          ]
        ]
      },
      "cannon": {
        "name": "M230 Chain Gun",
        "role": "Primary cannon",
        "fn": "A belly-mounted 30 mm M230 single-barrel chain gun hangs under the fuselage between the main wheels and slaves to the gunner's helmet sight, so it points wherever the crew looks. It fires high-explosive dual-purpose rounds that defeat light armour and troops out to about 1500 m.",
        "mats": [
          "Chrome-lined steel barrel",
          "Electric chain-driven action",
          "HEDP 30 mm ammunition"
        ],
        "specs": [
          [
            "Calibre",
            "30 mm"
          ],
          [
            "Rate",
            "≈625 rnd/min"
          ],
          [
            "Load",
            "1200 rounds"
          ],
          [
            "Aim",
            "Helmet-slaved"
          ]
        ]
      },
      "stubWing": {
        "name": "Stub Wings",
        "role": "Weapon pylons · lift",
        "fn": "Two short mid-fuselage wings each carry two hard-points and off-load the rotor by adding a little lift in fast cruise. Their drooped profile keeps the heavy weapon loads clear of the fuselage and rotor downwash.",
        "mats": [
          "Aluminium torque-box",
          "Composite skin",
          "BRU weapon racks"
        ],
        "specs": [
          [
            "Hard-points",
            "4 total"
          ],
          [
            "Span",
            "≈5.8 m"
          ],
          [
            "Load",
            "Rockets · missiles"
          ],
          [
            "Function",
            "Pylons + lift"
          ]
        ]
      },
      "weapons": {
        "name": "Rockets & Hellfires",
        "role": "Ordnance",
        "fn": "Each wing mounts a 19-shot Hydra-70 rocket pod inboard and a four-rail launcher of AGM-114 Hellfire laser-guided anti-tank missiles outboard. The Hellfires kill main battle tanks beyond 8 km while the rockets saturate soft and area targets.",
        "mats": [
          "Hydra-70 folding-fin rockets",
          "AGM-114 Hellfire missiles",
          "M299 smart launcher"
        ],
        "specs": [
          [
            "Rockets",
            "2 × 19-tube pods"
          ],
          [
            "Missiles",
            "up to 16 Hellfire"
          ],
          [
            "Hellfire range",
            "≈8+ km"
          ],
          [
            "Guidance",
            "Semi-active laser"
          ]
        ]
      },
      "engine": {
        "name": "Twin T700 Turboshafts",
        "role": "Powerplant",
        "fn": "Two General Electric T700 turboshaft engines sit in nacelles either side of the rotor mast and drive a common gearbox. Their upturned \"black hole\" infra-red suppressors mix cool air into the exhaust to defeat heat-seeking missiles.",
        "mats": [
          "Nickel super-alloy turbine",
          "Titanium compressor",
          "Black-hole IR suppressor"
        ],
        "specs": [
          [
            "Engines",
            "2 × GE T700"
          ],
          [
            "Power",
            "≈2 × 1490 kW"
          ],
          [
            "Layout",
            "Side nacelles"
          ],
          [
            "Exhaust",
            "IR-suppressed"
          ]
        ]
      },
      "mainRotor": {
        "name": "Main Rotor",
        "role": "Lift · thrust · control",
        "fn": "Four fully-articulated composite blades with swept tips mount on a steel-and-elastomeric hub atop the mast. The blades use a laminated stainless-steel spar and composite skin tough enough to keep flying after a 23 mm cannon strike.",
        "mats": [
          "Stainless-steel spar blades",
          "Composite / fibreglass skin",
          "Elastomeric lead-lag bearings"
        ],
        "specs": [
          [
            "Blades",
            "4"
          ],
          [
            "Diameter",
            "14.63 m"
          ],
          [
            "Tip",
            "Swept"
          ],
          [
            "RPM",
            "≈289"
          ]
        ]
      },
      "tailRotor": {
        "name": "Tail Rotor & Fin",
        "role": "Anti-torque · yaw",
        "fn": "A four-blade tail rotor set in an offset twin-pair arrangement on the port side of the swept vertical fin cancels the main-rotor torque and gives yaw control. The load-bearing fin also carries flight loads and the low-set stabilator.",
        "mats": [
          "Composite blades",
          "Steel pitch housing",
          "Load-bearing fin"
        ],
        "specs": [
          [
            "Blades",
            "4"
          ],
          [
            "Diameter",
            "2.79 m"
          ],
          [
            "Fin",
            "Swept · load-bearing"
          ],
          [
            "Side",
            "Port"
          ]
        ]
      },
      "stabilator": {
        "name": "Stabilator",
        "role": "Pitch control",
        "fn": "A low-mounted all-moving horizontal tailplane under the fin that the flight computer tilts with airspeed to hold the fuselage level and steady the gun platform. It unloads the rotor in a dive and improves pitch control at speed.",
        "mats": [
          "Composite skin",
          "Electro-mechanical actuator"
        ],
        "specs": [
          [
            "Type",
            "All-moving"
          ],
          [
            "Control",
            "Computer-scheduled"
          ],
          [
            "Span",
            "3.3 m"
          ],
          [
            "Position",
            "Low aft"
          ]
        ]
      },
      "gear": {
        "name": "Landing Gear",
        "role": "Ground contact",
        "fn": "A fixed tail-dragger undercarriage with two tall, trailing-arm main wheels and a small castoring tail wheel. The long energy-absorbing struts give the weapon pylons ground clearance and crush on a crash to save the crew.",
        "mats": [
          "Trailing-arm oleo struts",
          "High-strength steel",
          "Energy-absorbing stroke",
          "Rubber tyres"
        ],
        "specs": [
          [
            "Type",
            "Fixed tail-dragger"
          ],
          [
            "Mains",
            "2 tall"
          ],
          [
            "Tail",
            "Castoring wheel"
          ],
          [
            "Role",
            "Crashworthy"
          ]
        ]
      }
    }
  },
  {
    "id": "chinook",
    "tab": "CH-47 CHINOOK",
    "file": "./assets/models/chinook.glb",
    "info": {
      "name": "CH-47 Chinook",
      "variant": "Boeing · Heavy-Lift Transport",
      "role": "Heavy transport",
      "origin": "United States",
      "year": "In service 1962",
      "desc": "A twin-engine, tandem-rotor heavy-lift helicopter with two overlapping three-blade rotors and no tail rotor. In service since 1962, it hauls troops, artillery, vehicles and slung cargo for armies worldwide and remains one of the most capable lifters ever built.",
      "specs": [
        [
          "Crew",
          "3 + 33–55 troops"
        ],
        [
          "Length",
          "≈30.1 m (incl. rotors)"
        ],
        [
          "Rotor",
          "18.3 m × 2 · 3-blade each"
        ],
        [
          "Max speed",
          "≈315 km/h"
        ],
        [
          "Engines",
          "2 × Lycoming/Honeywell T55"
        ],
        [
          "Payload",
          "≈10,000 kg"
        ]
      ]
    },
    "parts": {
      "fuselage": {
        "name": "Fuselage",
        "role": "Primary airframe · cargo hull",
        "fn": "The long, tall, slab-sided aluminium hull is one big watertight cargo box with a flat cabin floor running the whole length. It carries up to 33–55 troops or heavy vehicles, with the tandem rotor pylons, engines and fuel all hung off this single load-bearing structure.",
        "mats": [
          "Aluminium-alloy frames",
          "Riveted stressed skin",
          "Watertight sealed hull",
          "Roller-equipped cargo floor"
        ],
        "specs": [
          [
            "Cabin",
            "33–55 troops"
          ],
          [
            "Floor length",
            "≈9.3 m"
          ],
          [
            "Width",
            "≈2.3 m"
          ],
          [
            "Floor",
            "Flat · roller rails"
          ]
        ]
      },
      "cockpit": {
        "name": "Cockpit",
        "role": "Crew station · flight deck",
        "fn": "Two pilots sit side-by-side behind a stepped, multi-panel windscreen with downward-looking chin bubble windows for precise load placement and brown-out landings. The glazing wraps around the blunt nose giving a wide field of view over the cargo hook work below.",
        "mats": [
          "Multi-pane windscreen",
          "Chin bubble vision panels",
          "Armoured crew seats"
        ],
        "specs": [
          [
            "Pilots",
            "2 side-by-side"
          ],
          [
            "Crew",
            "3 (+flight engineer)"
          ],
          [
            "Vision",
            "Chin bubbles"
          ],
          [
            "Windscreen",
            "Stepped"
          ]
        ]
      },
      "frontPylon": {
        "name": "Forward Rotor Pylon",
        "role": "Transmission · rotor mount",
        "fn": "A short raised hump above the cockpit houses the forward transmission that drives the front rotor. Drive shafts run back along the cabin roof to synchronise it with the rear rotor so the overlapping blades never collide.",
        "mats": [
          "Magnesium gearbox casing",
          "Composite fairing",
          "Steel drive mast"
        ],
        "specs": [
          [
            "Houses",
            "Forward transmission"
          ],
          [
            "Height",
            "Low (over cabin)"
          ],
          [
            "Drive",
            "Synchronising shaft"
          ]
        ]
      },
      "rearPylon": {
        "name": "Rear Rotor Pylon",
        "role": "Tall swept pylon · engine bay",
        "fn": "The tall, aft-swept rear pylon is the tallest point of the aircraft and carries the rear rotor well above and behind the front one. Its base holds the aft transmission and the two engines, and its broad fin shape also steadies the aircraft in forward flight.",
        "mats": [
          "Load-bearing fin structure",
          "Aft transmission bay",
          "Combining gearbox"
        ],
        "specs": [
          [
            "Position",
            "Aft · swept back"
          ],
          [
            "Tallest",
            "Yes"
          ],
          [
            "Holds",
            "Engines + aft gearbox"
          ]
        ]
      },
      "engine": {
        "name": "Twin Turboshaft Engines",
        "role": "Powerplant",
        "fn": "Two Lycoming/Honeywell T55 turboshaft engines are slung on the sides at the base of the rear pylon, feeding power forward and aft through a combining gearbox to both rotors. If one engine fails the other can still drive both rotors, and the large round exhausts vent sideways and rearward.",
        "mats": [
          "Nickel super-alloy turbines",
          "Combining gearbox",
          "Round metal exhaust ducts"
        ],
        "specs": [
          [
            "Engines",
            "2 × T55"
          ],
          [
            "Power",
            "≈2 × 3,500–4,800 shp"
          ],
          [
            "Feature",
            "Either engine drives both rotors"
          ]
        ]
      },
      "ramp": {
        "name": "Rear Loading Ramp",
        "role": "Cargo loading · access",
        "fn": "The full-width hydraulic ramp at the back lowers to the ground so trucks, pallets and troops can drive or walk straight into the cargo bay. It can also be left open in flight for loading slung gear or air-dropping cargo.",
        "mats": [
          "Hydraulic actuation",
          "Aluminium ramp deck",
          "Non-slip walkway"
        ],
        "specs": [
          [
            "Width",
            "Full cabin width"
          ],
          [
            "Use",
            "Vehicles · pallets · troops"
          ],
          [
            "In-flight",
            "Can open"
          ]
        ]
      },
      "sponson": {
        "name": "Side Sponsons",
        "role": "Fuel tanks · gear fairing",
        "fn": "Two long streamlined fairings run low along each side of the fuselage. They hold the main fuel tanks and form the mounting structure for the fixed landing gear, keeping the cabin floor completely clear for cargo.",
        "mats": [
          "Self-sealing fuel cells",
          "Aluminium fairing skin",
          "Gear mounting beams"
        ],
        "specs": [
          [
            "Fuel",
            "Internal main tanks"
          ],
          [
            "Also",
            "Landing-gear mounts"
          ],
          [
            "Count",
            "2 (one per side)"
          ]
        ]
      },
      "gear": {
        "name": "Landing Gear",
        "role": "Ground contact",
        "fn": "A fixed quadricycle undercarriage with four wheels mounted on the sponsons — two forward and two aft. The twin rear wheels steer, letting the big helicopter pivot tightly on the ground, and the sprung struts absorb heavy cargo landings.",
        "mats": [
          "Fixed non-retracting legs",
          "Oleo shock struts",
          "Steerable aft wheels"
        ],
        "specs": [
          [
            "Type",
            "Fixed quadricycle"
          ],
          [
            "Wheels",
            "4 (2 fwd · 2 aft)"
          ],
          [
            "Aft wheels",
            "Steerable"
          ]
        ]
      },
      "frontRotor": {
        "name": "Forward Main Rotor",
        "role": "Lift · thrust (front)",
        "fn": "The forward of the two big three-blade rotors. It turns opposite to the rear rotor so their torques cancel — that is why the Chinook needs no tail rotor. The two discs overlap above the cabin and are geared together so the blades always interleave safely.",
        "mats": [
          "Fibreglass spar blades",
          "Titanium hub",
          "Counter-rotating (opposite rear)"
        ],
        "specs": [
          [
            "Blades",
            "3"
          ],
          [
            "Diameter",
            "18.3 m"
          ],
          [
            "Turns",
            "Opposite rear rotor"
          ],
          [
            "Disc",
            "Overlaps rear"
          ]
        ]
      },
      "rearRotor": {
        "name": "Rear Main Rotor",
        "role": "Lift · thrust (rear) · anti-torque",
        "fn": "The rear three-blade rotor sits higher and further back on the tall pylon so its disc clears and overlaps the front one. Running opposite to the front rotor, this tandem layout both lifts the aircraft and balances torque, removing the need for a tail rotor and putting all engine power into lift.",
        "mats": [
          "Fibreglass spar blades",
          "Titanium hub",
          "Raised to overlap front disc"
        ],
        "specs": [
          [
            "Blades",
            "3"
          ],
          [
            "Diameter",
            "18.3 m"
          ],
          [
            "Turns",
            "Opposite front rotor"
          ],
          [
            "Mounting",
            "High · aft pylon"
          ]
        ]
      }
    }
  },
  {
    "id": "hind",
    "tab": "Mi-24 HIND",
    "file": "./assets/models/hind.glb",
    "info": {
      "name": "Mi-24 Hind",
      "variant": "Mil · Attack + Transport Gunship",
      "role": "Gunship / Assault transport",
      "origin": "Soviet Union / Russia",
      "year": "In service 1972",
      "desc": "A heavily armoured Soviet gunship that is unique in combining a hard-hitting weapons fit with a sealed cabin for up to eight troops. Nicknamed the \"flying tank\", it can strafe a target with rockets, missiles and a chin gun and then land to insert or recover its infantry squad.",
      "specs": [
        [
          "Crew",
          "2–3 + up to 8 troops"
        ],
        [
          "Length",
          "~17.5 m"
        ],
        [
          "Rotor",
          "17.3 m · 5-blade"
        ],
        [
          "Max speed",
          "~335 km/h"
        ],
        [
          "Engines",
          "2 × Isotov TV3-117"
        ],
        [
          "Armament",
          "12.7 mm gun + rockets + ATGM"
        ]
      ]
    },
    "parts": {
      "fuselage": {
        "name": "Fuselage",
        "role": "Primary airframe",
        "fn": "A long, heavily-armoured all-metal hull that is fat in the forward crew-and-cabin section and tapers into a slim tail boom. Behind the two-man cockpit sits a sealed troop bay — the Hind is unique in carrying up to eight soldiers while still fighting like a gunship.",
        "mats": [
          "Welded steel / aluminium frames",
          "Titanium cockpit tub armour",
          "Self-sealing fuel tanks"
        ],
        "specs": [
          [
            "Length",
            "~17.5 m"
          ],
          [
            "Cabin",
            "Up to 8 troops"
          ],
          [
            "Armour",
            "Titanium tub"
          ],
          [
            "Config",
            "Gunship + transport"
          ]
        ]
      },
      "cockpit": {
        "name": "Tandem Double-Bubble Canopy",
        "role": "Crew station",
        "fn": "The Hind's unmistakable feature: a low bubble canopy for the weapons officer at the very nose, with a second bubble canopy for the pilot stepped up and back behind it. Both crew sit in heavily glazed, armoured stations stacked one above the other.",
        "mats": [
          "Bullet-resistant laminated glass",
          "Armoured bulkhead between bubbles",
          "Steel canopy frames"
        ],
        "specs": [
          [
            "Crew",
            "2–3"
          ],
          [
            "Layout",
            "Tandem stepped"
          ],
          [
            "Front",
            "Gunner (low)"
          ],
          [
            "Rear",
            "Pilot (raised)"
          ]
        ]
      },
      "sensor": {
        "name": "Chin Turret & Sensors",
        "role": "Gun · targeting",
        "fn": "A powered chin turret under the nose carries a 12.7 mm machine gun that the weapons officer slews onto targets, flanked by low-light and infra-red sensor blisters for aiming in poor visibility. It lets the Hind strafe ground targets independently of the fixed wing weapons.",
        "mats": [
          "Gyro-stabilised turret",
          "12.7 mm Yak-B gun",
          "IR / low-light optics"
        ],
        "specs": [
          [
            "Turret",
            "Chin, powered"
          ],
          [
            "Gun",
            "12.7 mm 4-barrel"
          ],
          [
            "Sensors",
            "FLIR · searchlight"
          ]
        ]
      },
      "stubWing": {
        "name": "Anhedral Stub Wings",
        "role": "Lift · weapon pylons",
        "fn": "Short mid-fuselage wings that droop sharply downward (anhedral) and carry up to six weapon pylons. In fast forward flight they offload the rotor by producing a quarter of the lift, and they double the Hind's weapon capacity over a pure helicopter.",
        "mats": [
          "Metal torsion-box spar",
          "Six hardpoints",
          "Endplate launch rails"
        ],
        "specs": [
          [
            "Hardpoints",
            "6"
          ],
          [
            "Dihedral",
            "Anhedral (droop)"
          ],
          [
            "Lift share",
            "~25% in cruise"
          ]
        ]
      },
      "weapons": {
        "name": "Rocket Pods & ATGMs",
        "role": "Firepower",
        "fn": "The wings carry B-8/UB-type unguided rocket pods on the inner pylons and radio-guided anti-tank missiles on the wingtip rails, so one aircraft can hit soft targets, fortifications and armour in a single pass.",
        "mats": [
          "57/80 mm rocket pods",
          "Shturm/Ataka ATGM tubes",
          "Pylon ejector racks"
        ],
        "specs": [
          [
            "Rockets",
            "2 × pods"
          ],
          [
            "ATGM",
            "4 × wingtip"
          ],
          [
            "Guns",
            "Chin 12.7 mm"
          ]
        ]
      },
      "engine": {
        "name": "Twin Turboshafts",
        "role": "Powerplant",
        "fn": "Two Isotov TV3-117 turboshaft engines sit side-by-side above the cabin, breathing through the Hind's distinctive round dust-filtered intakes and driving the single main gearbox. They give the heavy gunship its high cruise speed and good hot-and-high performance.",
        "mats": [
          "TV3-117 turboshaft",
          "PZU dust filters",
          "Common main gearbox"
        ],
        "specs": [
          [
            "Engines",
            "2 × Isotov TV3-117"
          ],
          [
            "Intakes",
            "Round, filtered"
          ],
          [
            "Drive",
            "Single main gearbox"
          ]
        ]
      },
      "mainRotor": {
        "name": "Five-Blade Main Rotor",
        "role": "Lift · thrust · control",
        "fn": "A tall rotor head carries five all-metal blades — one more than most gunships — to lift the Hind's heavy combined weapon and troop load. The whole disc tilts to drive the aircraft and gives it an unusually high top speed for an armed helicopter.",
        "mats": [
          "Metal spar blades",
          "Steel / titanium hub",
          "Hydraulic swashplate"
        ],
        "specs": [
          [
            "Blades",
            "5"
          ],
          [
            "Diameter",
            "17.3 m"
          ],
          [
            "Top speed",
            "~335 km/h"
          ],
          [
            "RPM",
            "~240"
          ]
        ]
      },
      "tailRotor": {
        "name": "Tail Rotor & Fin",
        "role": "Anti-torque · yaw",
        "fn": "A three-blade tail rotor mounted on the port side near the top of a swept load-bearing fin cancels the main-rotor torque and gives yaw control. Small horizontal stabilisers at the base of the boom trim the aircraft in pitch through its speed range.",
        "mats": [
          "Composite / metal blades",
          "Load-bearing swept fin",
          "Trim stabilisers"
        ],
        "specs": [
          [
            "Blades",
            "3"
          ],
          [
            "Side",
            "Port (left)"
          ],
          [
            "Fin",
            "Swept, offset"
          ]
        ]
      },
      "gear": {
        "name": "Retractable Tricycle Gear",
        "role": "Ground contact",
        "fn": "A tricycle undercarriage — a single nose wheel forward and two larger main wheels — that normally folds up in flight to cut drag and is shown here extended. The long oleo struts absorb the shock of landings carrying a full weapon and troop load.",
        "mats": [
          "Oleo-pneumatic struts",
          "Twin-tyre main units",
          "Retraction jacks"
        ],
        "specs": [
          [
            "Type",
            "Retractable tricycle"
          ],
          [
            "Nose",
            "1 wheel"
          ],
          [
            "Mains",
            "2 wheels"
          ]
        ]
      }
    }
  }
];
