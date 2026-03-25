# Dr. Creep Asset Definitions
# Using Rich Markup: [color]text[/]

ASSETS = {
    "player": {
        "animations": {
            "idle": {
                "frames": [
                    [
                        "   ",
                        " [yellow]O [/] ",
                       r"[blue]/|\ [/]",
                        " [blue]| [/] ",
                        " [blue]| [/] ",
                       r"[green]/ \ [/]"
                    ]
                ],
                "speed": 0
            },
            "walk_right": {
                "frames": [
                    ["   ", 
                     " [yellow]O[/] ", 
                     "[blue] |=[/]", 
                     " [blue]|[/] ", 
                     " [blue]|[/] ", 
                    r"[green] |\ [/]"],
                    ["   ", 
                     " [yellow]O[/] ", 
                     "[blue] |=[/]", 
                     " [blue]|[/] ", 
                     " [blue]|[/] ", 
                    r"[green]/ \ [/]"],
                    ["   ", 
                     " [yellow]O[/] ", 
                     "[blue] |=[/]", 
                     " [blue]|[/] ", 
                     " [blue]|[/] ", 
                     "[green]/|  [/]"]
                ],
                "speed": 4
            },
            "walk_left": {
                "frames": [
                    ["   ", 
                     " [yellow]O[/] ", 
                     "[blue]=| [/]", 
                     " [blue]|[/] ", 
                     " [blue]|[/] ", 
                     "[green]/| [/]"],
                    ["   ", 
                     " [yellow]O[/] ", 
                     "[blue]=| [/]", 
                     " [blue]|[/] ", 
                     " [blue]|[/] ", 
                    r"[green]/ \ [/]"],
                    ["   ", 
                     " [yellow]O[/] ", 
                     "[blue]=| [/]", 
                     " [blue]|[/] ", 
                     " [blue]|[/] ", 
                    r"[green] |\ [/]"]
                ],
                "speed": 4
            },
            "action": {
                "frames": [["   ", 
                            " [yellow]O[/] ", 
                           r"[blue]\|/[/]", 
                            " [blue]|[/] ", 
                            " [blue]|[/] ", 
                           r"[green]/ \ [/]"]],
                "speed": 0
            }
        }
    },
    "mummy": {
        "animations": {
            "idle": {
                "frames": [
                    ["   ", 
                     " [white]O[/] ", 
                     " [white]|[/] ", 
                     " [white]|[/] ", 
                     " [white]|[/] ", 
                    r"[white]/ \ [/]"]],
                "speed": 0
            },
            "walk_right": {
                "frames": [
                    ["   ", 
                     " [white]O [/]", 
                     " [white]|=[/]", 
                     " [white]| [/]", 
                     " [white]| [/]", 
                    r"[white]/ \ [/]"],
                    ["   ", 
                     " [white]O [/]", 
                     " [white]|=[/]", 
                     " [white]| [/]", 
                     " [white]| [/]", 
                    r"[white] |\ [/]"]
                ],
                "speed": 4
            },
            "walk_left": {
                "frames": [
                    ["   ", 
                     "[white] O[/] ", 
                     "[white]=|[/] ", 
                     "[white] |[/] ", 
                     "[white] |[/] ", 
                    r"[white]/ \ [/]"],
                    ["   ", 
                     "[white] O[/] ", 
                     "[white]=|[/] ", 
                     "[white] |[/] ", 
                     "[white] |[/] ", 
                     "[white]/|[/]"]
                ],
                "speed": 4
            }
        }
    },
    "frankie": {
        "animations": {
            "idle": {
                "frames": [
                    ["   ", 
                     " [green]O[/] ", 
                    r"[green]/|\ [/]", 
                     " [green]|[/] ", 
                     " [green]|[/] ", 
                    r"[green]/ \ [/]"]],
                "speed": 0
            },
            "walk_right": {
                "frames": [
                    ["   ", 
                     " [green]O [/]", 
                     " [green]|=[/]", 
                     " [green]| [/]", 
                     " [green]| [/]", 
                    r"[green] |\ [/]"],
                    ["   ", 
                     " [green]O [/]", 
                     " [green]|=[/]", 
                     " [green]| [/]", 
                     " [green]| [/]", 
                    r"[green]/ \ [/]"]
                ],
                "speed": 6
            },
            "walk_left": {
                "frames": [
                    ["   ", 
                     "[green] O[/] ", 
                     "[green]=|[/] ", 
                     "[green] |[/] ", 
                     "[green] |[/] ", 
                    r"[green]/| [/]"],
                    ["   ", 
                     "[green] O[/] ", 
                     "[green]=|[/] ", 
                     "[green] |[/] ", 
                     "[green] |[/] ", 
                    r"[green]/ \ [/]"]
                ],
                "speed": 6
            }
        }
    },
    "door": {
        "frames": [
               [ # Closed
                "[white]----------[/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white]----------"
            ],
               [ # Partial
                "[white]----------[/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][[yellow]________[/]][/]",
                "[white][[next_room_color]/░░░░░░░[/]][/]",
                "[white]----------"
            ],
               [ # Partial
                "[white]----------[/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][[yellow]________[/]][/]",
                "[white][  [next_room_color]/░░░░░[/]][/]",
                "[white][ [next_room_color]/______[/]][/]",
                "[white][[next_room_color]/░░░░░░░[/]][/]",
                "[white]----------"
            ],
               [ # Open (with perspective path)
                "[white]----------[/]",
                "[white][     [next_room_color]___[/]][/]",
                "[white][    [next_room_color]/░░░[/]][/]",
                "[white][   [next_room_color]/____[/]][/]",
                "[white][  [next_room_color]/░░░░░[/]][/]",
                "[white][ [next_room_color]/______[/]][/]",
                "[white][[next_room_color]/░░░░░░░[/]][/]",
                "[white]----------"
            ]
        ]
    },
    "teleport_cabin": {
        "template": [
            "[obj_color]======[/]",
            "[obj_color][    ][/]",
            "[obj_color][    ][/]",
            "[obj_color][    ][/]",
            "[obj_color][    ][/]",
            "[obj_color][    ][/]",
            "[obj_color][    ][/]",
            "[obj_color][    ][/]"
        ]
    },
    "teleport_target": {
        "template": ["[obj_color]●[/]"]
    },
    "conveyor": {
        "animations": {
            "left": {
                "frames": [
                    [r"[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[/]"],
                    [r"[blue][gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~[blue][/]"],
                    [r"[blue][gray]~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue][/]"],
                ],
                "speed": 4
            },
            "right": {
                "frames": [
                    ["[blue]/  /  / [/]"],
                    ["[blue] /  /  /[/]"],
                    ["[blue]  /  /  [/]"],
                ],
                "speed": 4
            },
            "off": {
                "frames": [["[blue]~~~~~~~~~~[/]"]],
                "speed": 0
            }
        }
    },
    "doorbell": {"template": ["[white]●[/]"]},
    "key": {"template": ["[obj_color]k[/]"]},
    "lock": {"template": ["[obj_color]X[/]"]},
    "forcefield_switch": {"template": ["[cyan]S[/]"]},
    "forcefield": {
        "states": {
            0: ["[cyan]z[/]", " ", " ", " ", " ", " ", " ", " "],
            1: ["[cyan]z[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]"]
        }
    },
    "mummy_tomb": {
        "template": [
            "[red]#####[/]",
            "[red]#####[/]",
            "[red]#####[/]"
        ]
    },
    "lightning_machine": {"template": ["[cyan](O)[/]"]},
    "lightning_switch": {"template": ["[cyan][[yellow]T[/]][/]"]},
    "trapdoor_switch": {"template": ["[cyan]o[/]"]},
    "raygun": {"template": ["[red]>====>[/]"]},
    "raygun_switch": {
        "template": [
            " [cyan]^[/] ",
            " [cyan]O[/] ",
            " [cyan]v[/] "
        ]
    },
    "mummy_release": {"template": ["[white]M[/]"]}
}
