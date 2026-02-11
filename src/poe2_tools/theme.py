import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class ThemeManager:
    """
    Manages the application theme.
    Style: Minimalist Dark (High Contrast, Deep Backgrounds, Functional Accents)
    """
    
    # Colors (Refined Usagi/Chiikawa Palette)
    # User Provided: Yellows, Pinks, and Warm Whites
    
    # Usagi Theme Colors (Final Polish)
    COLOR_BG_MAIN = "#fff2d5"      # Warm Cream (Main Background)
    COLOR_BG_SIDEBAR = "#8a7a6a"   # Muted Brown (Sidebar)
    COLOR_BG_CARD = "#fff2d5"      # Same as main background
    COLOR_BG_INPUT = "#ffffff"     # White (Restored from Pink)
    COLOR_BTN_BG = "#ffffff"       # Global button base background
    
    COLOR_PRIMARY = "#8a7a6a"      # Match Sidebar for primary elements
    COLOR_SUCCESS = "#8a7a6a"      # Match Primary (No Green in Usagi Theme)
    COLOR_DANGER = "#E57373"       # Red (Danger)
    COLOR_WARNING = "#D99B2B"      # Deep Yellow (Warning)
    
    COLOR_TEXT_MAIN = "#000000"    # Black (Main Text)
    COLOR_TEXT_SIDEBAR = "#FFFFFF" # White (Sidebar Text)
    COLOR_TEXT_MUTED = "#5D4037"   # Dark Brown (Muted Text)
    COLOR_BORDER = "#1E1E1E"       # Black (Borders)
    COLOR_TEXT_MUTED = "#5D4037"   # Dark Brown (Sidebar Text on Yellow) - Changed from Soft Black
    COLOR_BORDER = "#1E1E1E"       # Black (Borders)
    
    # Specific Module Colors (Auto Potion) - "Basic Principles"
    COLOR_HP = "#FF4D4D"           # Bright Red (HP)
    COLOR_MP = "#4C8EFF"           # Bright Blue (MP)

    FONT_CN = "Microsoft YaHei"
    FONT_EN = "Times New Roman"
    FONT_SIZE = 10
    FONT_WEIGHT = "bold"

    @staticmethod
    def setup_styles(style: ttk.Style):
        """
        Configure custom styles for the application.
        """
        # 1. Sync ttkbootstrap Internal Colors (Fixes "Blue" active states)
        # This is critical because bootstyle="primary" uses these internal values
        style.colors.primary = ThemeManager.COLOR_PRIMARY
        style.colors.success = ThemeManager.COLOR_SUCCESS
        style.colors.warning = ThemeManager.COLOR_WARNING
        style.colors.danger = ThemeManager.COLOR_HP  # Use HP Red for Danger/Red
        style.colors.info = ThemeManager.COLOR_MP    # Use MP Blue for Info/Blue
        
        # 2. Main Styles
        # Default Label should match the Card background since most content is on cards
        style.configure(
            ".",
            background=ThemeManager.COLOR_BG_MAIN,
            foreground=ThemeManager.COLOR_TEXT_MAIN,
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        )
        style.configure("TLabel", background=ThemeManager.COLOR_BG_CARD, foreground=ThemeManager.COLOR_TEXT_MAIN)
        
        # 8. LabelFrame Borders - Fixing "Layer" issues
        # Labelframes are used inside Cards, so they must use Card Background
        style.configure(
            "TLabelframe",
            background=ThemeManager.COLOR_BG_CARD,
            bordercolor=ThemeManager.COLOR_BG_CARD,
            borderwidth=0,
            relief="flat"
        )
        style.configure(
            "TLabelframe.Label",
            background=ThemeManager.COLOR_BG_CARD,
            foreground=ThemeManager.COLOR_PRIMARY,
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT)
        )

        # 2. Card Style (Minimalist Container)
        style.configure(
            "Card.TFrame",
            background=ThemeManager.COLOR_BG_CARD,
            relief="flat",
            borderwidth=0
        )
        
        # ... (rest of styles remain similar, skipping to Checkbutton fix) ...

    # We need to access the rest of the file to splice this correctly or I can just update the checkbutton block
    # Retargeting just the color sync and checkbutton block for clarity/safety? 
    # The tool requires contiguous block. I will replace the START of setup_styles to inject color sync, 
    # and then a second call for the Checkbuttons if needed, or do it all in one large replacement if safer. 
    # Given the file size, I will restart the Checkbutton section replacement to include the loop improvements.

    # Wait, the instruction above was to "Sync ttkbootstrap internal colors".
    # I should place that at the TOP of setup_styles.
    
    # And then fix the Checkbuttons at the bottom.
    # I'll do two edits.

        pass # Placeholder for logic construction in thought process

        # 2. Card Style (Minimalist Container)
        style.configure(
            "Card.TFrame",
            background=ThemeManager.COLOR_BG_CARD,
            relief="flat",
            borderwidth=0
        )
        
        # Card Title (Subtle, uppercase maybe?)
        style.configure(
            "Card.TLabel",
            background=ThemeManager.COLOR_BG_CARD,
            foreground=ThemeManager.COLOR_PRIMARY,
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT)
        )
        # Content Label (Inside Cards)
        style.configure(
            "Content.TLabel",
            background=ThemeManager.COLOR_BG_CARD,
            foreground=ThemeManager.COLOR_TEXT_MAIN
        )
        style.configure(
            "Cn.Content.TLabel",
            background=ThemeManager.COLOR_BG_CARD,
            foreground=ThemeManager.COLOR_TEXT_MAIN,
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        )

        # Main Background Frame (for outer containers)
        style.configure(
            "Main.TFrame",
            background=ThemeManager.COLOR_BG_MAIN
        )

        # Content Frame (for inner layout within Cards)
        style.configure(
            "Content.TFrame",
            background=ThemeManager.COLOR_BG_CARD,
            relief="flat",
            borderwidth=0
        )

        # 3. Sidebar Style
        style.configure(
            "Sidebar.TFrame",
            background=ThemeManager.COLOR_BG_SIDEBAR,
            relief="flat"
        )
        
        # Sidebar Button (Minimalist, text-only feel)
        style.configure(
            "Nav.TButton",
            background=ThemeManager.COLOR_BG_SIDEBAR,
            foreground=ThemeManager.COLOR_TEXT_SIDEBAR,
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
            borderwidth=0,
            focuscolor=ThemeManager.COLOR_BG_SIDEBAR,
            focusthickness=0,
            anchor="w",
            padding=(20, 15)
        )
        style.map(
            "Nav.TButton",
            background=[("active", ThemeManager.COLOR_BG_CARD), ("selected", ThemeManager.COLOR_BG_CARD)], # Use Card Color for hover
            foreground=[("active", ThemeManager.COLOR_TEXT_MAIN), ("selected", ThemeManager.COLOR_TEXT_MAIN)],
            relief=[("pressed", "flat"), ("!pressed", "flat")]
        )

        # 4. Inputs
        style.configure(
            "TEntry",
            fieldbackground=ThemeManager.COLOR_BG_INPUT, # Use Theme Input Color
            foreground=ThemeManager.COLOR_TEXT_MAIN,
            font=(ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
            borderwidth=0,
            relief="flat",
            bordercolor=ThemeManager.COLOR_BG_INPUT,
            insertcolor=ThemeManager.COLOR_TEXT_MAIN
        )
        style.map(
            "TEntry",
            fieldbackground=[("readonly", ThemeManager.COLOR_BG_INPUT), ("!readonly", ThemeManager.COLOR_BG_INPUT)],
            background=[("readonly", ThemeManager.COLOR_BG_INPUT), ("!readonly", ThemeManager.COLOR_BG_INPUT)]
        )
        style.configure(
            "Numeric.TEntry",
            fieldbackground=ThemeManager.COLOR_BG_INPUT,
            foreground=ThemeManager.COLOR_TEXT_MAIN,
            font=(ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
            borderwidth=0,
            relief="flat",
            bordercolor=ThemeManager.COLOR_BG_INPUT,
            insertcolor=ThemeManager.COLOR_TEXT_MAIN,
        )
        style.map(
            "Numeric.TEntry",
            fieldbackground=[("readonly", ThemeManager.COLOR_BG_INPUT), ("!readonly", ThemeManager.COLOR_BG_INPUT)],
            background=[("readonly", ThemeManager.COLOR_BG_INPUT), ("!readonly", ThemeManager.COLOR_BG_INPUT)],
        )

        # 5. Buttons
        style.configure(
            "TButton",
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
            background=ThemeManager.COLOR_BTN_BG,
            foreground=ThemeManager.COLOR_PRIMARY,
            bordercolor=ThemeManager.COLOR_BTN_BG,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "TButton",
            background=[
                ("active", ThemeManager.COLOR_PRIMARY),
                ("pressed", ThemeManager.COLOR_PRIMARY),
                ("selected", ThemeManager.COLOR_PRIMARY),
                ("disabled", ThemeManager.COLOR_BTN_BG),
            ],
            foreground=[
                ("active", ThemeManager.COLOR_BTN_BG),
                ("pressed", ThemeManager.COLOR_BTN_BG),
                ("selected", ThemeManager.COLOR_BTN_BG),
                ("disabled", ThemeManager.COLOR_TEXT_MUTED),
            ],
            bordercolor=[
                ("active", ThemeManager.COLOR_PRIMARY),
                ("pressed", ThemeManager.COLOR_PRIMARY),
                ("selected", ThemeManager.COLOR_PRIMARY),
                ("disabled", ThemeManager.COLOR_TEXT_MUTED),
            ],
        )
        
        # Force bootstyle colors to match ThemeManager (since style.colors update might be too late for some widgets)
        style_color_map = {
            "Primary": ThemeManager.COLOR_PRIMARY,
            "Secondary": ThemeManager.COLOR_TEXT_MUTED, # Use Muted Brown for Secondary
            "Success": ThemeManager.COLOR_SUCCESS,
            "Info": ThemeManager.COLOR_MP,         # Info maps to MP Blue
            "Warning": ThemeManager.COLOR_WARNING,
            "Danger": ThemeManager.COLOR_HP,       # Danger maps to HP Red
            "Light": ThemeManager.COLOR_BG_CARD,
            "Dark": ThemeManager.COLOR_TEXT_MAIN
        }
        
        for flavor, color_value in style_color_map.items():
            # Solid Button
            style.configure(
                f"{flavor}.TButton",
                background=ThemeManager.COLOR_BTN_BG,
                foreground=ThemeManager.COLOR_PRIMARY,
                bordercolor=ThemeManager.COLOR_BTN_BG,
                borderwidth=0,
                relief="flat",
            )
            style.map(
                f"{flavor}.TButton",
                background=[
                    ("active", ThemeManager.COLOR_PRIMARY),
                    ("pressed", ThemeManager.COLOR_PRIMARY),
                    ("selected", ThemeManager.COLOR_PRIMARY),
                    ("disabled", ThemeManager.COLOR_BTN_BG),
                ],
                foreground=[
                    ("active", ThemeManager.COLOR_BTN_BG),
                    ("pressed", ThemeManager.COLOR_BTN_BG),
                    ("selected", ThemeManager.COLOR_BTN_BG),
                    ("disabled", ThemeManager.COLOR_TEXT_MUTED),
                ],
                bordercolor=[
                    ("active", ThemeManager.COLOR_PRIMARY),
                    ("pressed", ThemeManager.COLOR_PRIMARY),
                    ("selected", ThemeManager.COLOR_PRIMARY),
                    ("disabled", ThemeManager.COLOR_TEXT_MUTED),
                ],
            )
            
            # Outline Button
            style.configure(
                f"{flavor}.Outline.TButton",
                background=ThemeManager.COLOR_BTN_BG,
                foreground=ThemeManager.COLOR_PRIMARY,
                bordercolor=ThemeManager.COLOR_BTN_BG,
                borderwidth=0,
                relief="flat",
            )
            style.map(
                f"{flavor}.Outline.TButton",
                background=[
                    ("active", ThemeManager.COLOR_PRIMARY),
                    ("pressed", ThemeManager.COLOR_PRIMARY),
                    ("selected", ThemeManager.COLOR_PRIMARY),
                    ("disabled", ThemeManager.COLOR_BTN_BG),
                ],
                foreground=[
                    ("active", ThemeManager.COLOR_BTN_BG),
                    ("pressed", ThemeManager.COLOR_BTN_BG),
                    ("selected", ThemeManager.COLOR_BTN_BG),
                    ("disabled", ThemeManager.COLOR_TEXT_MUTED),
                ],
                bordercolor=[
                    ("active", ThemeManager.COLOR_PRIMARY),
                    ("pressed", ThemeManager.COLOR_PRIMARY),
                    ("selected", ThemeManager.COLOR_PRIMARY),
                    ("disabled", ThemeManager.COLOR_TEXT_MUTED),
                ],
            )

        # Link buttons also follow same interaction rule
        style.configure(
            "Link.TButton",
            background=ThemeManager.COLOR_BTN_BG,
            foreground=ThemeManager.COLOR_PRIMARY,
            bordercolor=ThemeManager.COLOR_BTN_BG,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Link.TButton",
            background=[("active", ThemeManager.COLOR_PRIMARY), ("pressed", ThemeManager.COLOR_PRIMARY), ("selected", ThemeManager.COLOR_PRIMARY)],
            foreground=[("active", ThemeManager.COLOR_BTN_BG), ("pressed", ThemeManager.COLOR_BTN_BG), ("selected", ThemeManager.COLOR_BTN_BG)],
            bordercolor=[("active", ThemeManager.COLOR_PRIMARY), ("pressed", ThemeManager.COLOR_PRIMARY), ("selected", ThemeManager.COLOR_PRIMARY)],
        )

        # Persistent action buttons (used for start/stop toggle states)
        style.configure(
            "Action.TButton",
            background=ThemeManager.COLOR_BTN_BG,
            foreground=ThemeManager.COLOR_PRIMARY,
            bordercolor=ThemeManager.COLOR_BTN_BG,
            borderwidth=0,
            relief="flat",
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        )
        style.map(
            "Action.TButton",
            background=[("active", ThemeManager.COLOR_BG_MAIN), ("pressed", ThemeManager.COLOR_BG_MAIN)],
            foreground=[("active", ThemeManager.COLOR_TEXT_MAIN), ("pressed", ThemeManager.COLOR_TEXT_MAIN)],
            bordercolor=[("active", ThemeManager.COLOR_PRIMARY), ("pressed", ThemeManager.COLOR_PRIMARY)],
        )

        style.configure(
            "Action.Active.TButton",
            background=ThemeManager.COLOR_BG_MAIN,
            foreground=ThemeManager.COLOR_TEXT_MAIN,
            bordercolor=ThemeManager.COLOR_BG_MAIN,
            borderwidth=0,
            relief="flat",
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        )
        style.map(
            "Action.Active.TButton",
            background=[("active", ThemeManager.COLOR_BTN_BG), ("pressed", ThemeManager.COLOR_BTN_BG)],
            foreground=[("active", ThemeManager.COLOR_PRIMARY), ("pressed", ThemeManager.COLOR_PRIMARY)],
            bordercolor=[("active", ThemeManager.COLOR_BTN_BG), ("pressed", ThemeManager.COLOR_BTN_BG)],
        )

        # Mode toggle buttons (used in divine reforge mode switch)
        style.configure(
            "Mode.TButton",
            background=ThemeManager.COLOR_BTN_BG,
            foreground=ThemeManager.COLOR_PRIMARY,
            bordercolor=ThemeManager.COLOR_BTN_BG,
            borderwidth=0,
            relief="flat",
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        )
        style.map(
            "Mode.TButton",
            background=[("active", ThemeManager.COLOR_PRIMARY), ("pressed", ThemeManager.COLOR_PRIMARY)],
            foreground=[("active", ThemeManager.COLOR_BTN_BG), ("pressed", ThemeManager.COLOR_BTN_BG)],
            bordercolor=[("active", ThemeManager.COLOR_PRIMARY), ("pressed", ThemeManager.COLOR_PRIMARY)],
        )

        style.configure(
            "Mode.Active.TButton",
            background=ThemeManager.COLOR_PRIMARY,
            foreground=ThemeManager.COLOR_BTN_BG,
            bordercolor=ThemeManager.COLOR_PRIMARY,
            borderwidth=0,
            relief="flat",
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        )
        
        # 6. Additional Inputs (Spinbox, Combobox) - Fixing "Black" issues
        # Config for TSpinbox
        style.configure(
            "TSpinbox",
            fieldbackground=ThemeManager.COLOR_BG_INPUT,
            background=ThemeManager.COLOR_BG_INPUT,
            foreground=ThemeManager.COLOR_TEXT_MAIN,
            font=(ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
            arrowcolor=ThemeManager.COLOR_PRIMARY,
            borderwidth=1,
            relief="solid",
            insertcolor=ThemeManager.COLOR_TEXT_MAIN
        )
        style.map(
            "TSpinbox",
            fieldbackground=[("readonly", ThemeManager.COLOR_BG_INPUT), ("!readonly", ThemeManager.COLOR_BG_INPUT)],
            background=[("readonly", ThemeManager.COLOR_BG_INPUT), ("!readonly", ThemeManager.COLOR_BG_INPUT)]
        )

        # Config for TCombobox
        style.configure(
            "TCombobox",
            fieldbackground=ThemeManager.COLOR_BG_INPUT,
            background=ThemeManager.COLOR_BG_INPUT,
            foreground=ThemeManager.COLOR_TEXT_MAIN,
            font=(ThemeManager.FONT_EN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
            arrowcolor=ThemeManager.COLOR_PRIMARY,
            borderwidth=1,
            relief="solid",
            insertcolor=ThemeManager.COLOR_TEXT_MAIN
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", ThemeManager.COLOR_BG_INPUT), ("!readonly", ThemeManager.COLOR_BG_INPUT)],
            background=[("readonly", ThemeManager.COLOR_BG_INPUT), ("!readonly", ThemeManager.COLOR_BG_INPUT)],
            selectbackground=[("readonly", ThemeManager.COLOR_PRIMARY)],
            selectforeground=[("readonly", ThemeManager.COLOR_TEXT_MAIN)]
        )

        # 7. Checkbuttons & Radiobuttons
        style.configure(
            "TCheckbutton",
            background=ThemeManager.COLOR_BG_CARD, # Match card background usually
            foreground=ThemeManager.COLOR_TEXT_MAIN,
            indicatorcolor=ThemeManager.COLOR_BG_INPUT, # Checkbox inner
            indicatorrelief="solid",
            indicatorborderwidth=1
        )
        # Fix for "Round Toggle" having wrong background
        # We iterate through all standard colors to ensure the generated styles are caught
        toggle_styles = ["Round.Toggle.TCheckbutton", "Square.Toggle.TCheckbutton", "Toggle.TCheckbutton"]
        colors = ["Primary", "Secondary", "Success", "Info", "Warning", "Danger", "Light", "Dark"]
        
        # Add base styles
        targets = list(toggle_styles)
        # Add colored styles (e.g. Primary.Round.Toggle.TCheckbutton)
        for c in colors:
            for t in toggle_styles:
                targets.append(f"{c}.{t}")
        
        for ts in targets:
            style.configure(ts, background=ThemeManager.COLOR_BG_CARD)
            style.map(
                ts,
                background=[("active", ThemeManager.COLOR_BG_CARD), ("!active", ThemeManager.COLOR_BG_CARD), ("selected", ThemeManager.COLOR_BG_CARD)],
                fieldbackground=[("active", ThemeManager.COLOR_BG_CARD), ("!active", ThemeManager.COLOR_BG_CARD), ("selected", ThemeManager.COLOR_BG_CARD)]
            )

        style.configure(
             "TRadiobutton",
            background=ThemeManager.COLOR_BG_CARD,
            foreground=ThemeManager.COLOR_TEXT_MAIN,
            indicatorcolor=ThemeManager.COLOR_BG_INPUT
        )
        # Fix for Toolbutton styles if used
        style.configure(
            "Toolbutton",
            background=ThemeManager.COLOR_BTN_BG,
            foreground=ThemeManager.COLOR_PRIMARY,
            bordercolor=ThemeManager.COLOR_BTN_BG,
            borderwidth=0,
            relief="flat",
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        )
        style.map(
            "Toolbutton",
            background=[("active", ThemeManager.COLOR_PRIMARY), ("selected", ThemeManager.COLOR_PRIMARY)],
            foreground=[("active", ThemeManager.COLOR_BTN_BG), ("selected", ThemeManager.COLOR_BTN_BG)],
            bordercolor=[("active", ThemeManager.COLOR_BTN_BG), ("selected", ThemeManager.COLOR_BTN_BG)],
        )
        style.configure(
            "Outline.Toolbutton",
            background=ThemeManager.COLOR_BTN_BG,
            foreground=ThemeManager.COLOR_PRIMARY,
            bordercolor=ThemeManager.COLOR_BTN_BG,
            borderwidth=0,
            relief="flat",
            font=(ThemeManager.FONT_CN, ThemeManager.FONT_SIZE, ThemeManager.FONT_WEIGHT),
        )
        style.map(
            "Outline.Toolbutton",
            background=[("active", ThemeManager.COLOR_PRIMARY), ("selected", ThemeManager.COLOR_PRIMARY)],
            foreground=[("active", ThemeManager.COLOR_BTN_BG), ("selected", ThemeManager.COLOR_BTN_BG)],
            bordercolor=[("active", ThemeManager.COLOR_BTN_BG), ("selected", ThemeManager.COLOR_BTN_BG)],
        )

        # 8. LabelFrame Borders - Fixing "Black Rings"
        # 8. LabelFrame Borders - Merged into Main Styles section above
        # (This block removed to avoid duplication/confusion)
