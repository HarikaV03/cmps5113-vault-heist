"""
Course:      CMPS 5113 - Advanced Programming Language Concepts
Assignment:  Program 3 - Open-Ended OOP GUI Program (Vault Heist: Safe Cracker)
Author:      Harika Vemulapalli
Description: A risk-vs.-reward safe-cracking game built with Python tkinter.
             Players spin three vault dials toward target ranges while managing
             remaining turns and alarm Heat before locking each tumbler.
"""

import random
import tkinter as tk
from tkinter import messagebox


class Dial:
    """Represents a single vault tumbler with a target range and heat limit."""

    def __init__(
        self,
        dial_number: int,
        target_min: int,
        target_max: int,
        max_safe: int,
    ) -> None:
        self.dial_number = dial_number
        self.target_min = target_min
        self.target_max = target_max
        self.max_safe = max_safe
        self.value: int = 0
        self.locked: bool = False

    def spin(self) -> tuple[int, int, str]:
        """
        Applies a random spin delta to the dial and returns (delta, heat_added, note).
        """
        if self.locked:
            return 0, 0, f"Dial {self.dial_number} is already locked."

        # Mix of controlled and bigger jumps for risk/reward tension
        delta = random.choice([2, 3, 4, 6, 8, 10])
        self.value += delta
        heat_added = 6

        if self.value > self.max_safe:
            heat_added += 18
            overshoot = self.value - self.max_safe
            # Pull back slightly after tripping the danger zone
            self.value = max(0, self.target_max - 2)
            note = (
                f"Dial {self.dial_number} jumped +{delta} past safe limit "
                f"(+{overshoot} over)! Alarm spike! Pulled back to {self.value}."
            )
        elif self.is_in_target():
            note = f"Dial {self.dial_number} shifted +{delta} to {self.value} — right in the sweet spot!"
        else:
            note = f"Dial {self.dial_number} shifted +{delta} to {self.value} (Target: {self.target_min}-{self.target_max})."

        return delta, heat_added, note

    def is_in_target(self) -> bool:
        """Returns True if the current dial value is inside the target range."""
        return self.target_min <= self.value <= self.target_max

    def lock(self) -> tuple[bool, str]:
        """Attempts to lock the dial if it is within the target range."""
        if self.locked:
            return False, f"Dial {self.dial_number} is already locked."
        if not self.is_in_target():
            return (
                False,
                f"Dial {self.dial_number} is at {self.value} — must be between "
                f"{self.target_min} and {self.target_max} to lock safely!",
            )
        self.locked = True
        return True, f"Dial {self.dial_number} LOCKED at {self.value}!"


class VaultHeistGame:
    """Manages dials, turns, alarm heat, win/loss state, and overall tally."""

    MAX_TURNS: int = 14
    MAX_HEAT: int = 100

    def __init__(self) -> None:
        self.wins: int = 0
        self.losses: int = 0
        self.dials: list[Dial] = []
        self.active_index: int = 0
        self.turns_left: int = self.MAX_TURNS
        self.heat: int = 0
        self.round_over: bool = False
        self.status_message: str = ""
        self.new_heist()

    def new_heist(self) -> None:
        """Initializes a fresh 3-dial vault round with randomized target ranges."""
        t1_min = random.randint(10, 18)
        t2_min = random.randint(14, 22)
        t3_min = random.randint(12, 20)

        self.dials = [
            Dial(1, t1_min, t1_min + 4, t1_min + 9),
            Dial(2, t2_min, t2_min + 4, t2_min + 9),
            Dial(3, t3_min, t3_min + 4, t3_min + 9),
        ]
        self.active_index = 0
        self.turns_left = self.MAX_TURNS
        self.heat = 0
        self.round_over = False
        self.status_message = (
            "Heist started! Spin Dial 1 into its target range, then lock it before turns run out or Heat hits 100%."
        )

    def current_dial(self) -> Dial:
        """Returns the currently active dial."""
        return self.dials[self.active_index]

    def _advance_active_dial(self) -> None:
        """Moves active focus to the next unlocked dial, if any."""
        for idx in range(len(self.dials)):
            candidate = (self.active_index + idx) % len(self.dials)
            if not self.dials[candidate].locked:
                self.active_index = candidate
                return

    def _check_end_conditions(self) -> None:
        """Checks whether the player cracked all dials or triggered a loss."""
        if all(d.locked for d in self.dials):
            self.round_over = True
            self.wins += 1
            self.status_message = (
                f"VAULT CRACKED! All 3 dials locked with {self.turns_left} turn(s) and {self.heat}% Heat!"
            )
            return

        if self.heat >= self.MAX_HEAT:
            self.heat = self.MAX_HEAT
            self.round_over = True
            self.losses += 1
            self.status_message = "ALARM TRIPPED! Heat hit 100% — vault lockdown! Click 'New Heist' to try again."
            return

        if self.turns_left <= 0:
            self.turns_left = 0
            self.round_over = True
            self.losses += 1
            self.status_message = "OUT OF TURNS! Security arrived before all dials were locked. Click 'New Heist'."

    def spin_active_dial(self) -> None:
        """Spins the active dial, spends 1 turn, and updates alarm heat."""
        if self.round_over:
            self.status_message = "This round is over. Click 'New Heist' to play again."
            return

        dial = self.current_dial()
        _, heat_added, note = dial.spin()
        self.turns_left -= 1
        self.heat = min(self.MAX_HEAT, self.heat + heat_added)
        self.status_message = f"{note} (-1 turn, +{heat_added}% Heat)"
        self._check_end_conditions()

    def lock_active_dial(self) -> None:
        """Attempts to lock the active dial (costs 1 turn on a valid lock)."""
        if self.round_over:
            self.status_message = "This round is over. Click 'New Heist' to play again."
            return

        dial = self.current_dial()
        ok, msg = dial.lock()
        if not ok:
            self.status_message = msg
            return

        self.turns_left -= 1
        self._advance_active_dial()
        self.status_message = f"{msg} (-1 turn)"
        self._check_end_conditions()


class VaultHeistGUI:
    """Tkinter GUI for Vault Heist: Safe Cracker."""

    def __init__(self, root: tk.Tk, game: VaultHeistGame) -> None:
        self.root = root
        self.game = game

        self.root.title("Vault Heist: Safe Cracker — CMPS 5113")
        self.root.geometry("760x470")
        self.root.minsize(680, 420)

        self._build_ui()
        self._refresh_ui()

    def _build_ui(self) -> None:
        # Top Header & Telemetry
        top_frame = tk.Frame(self.root, padx=16, pady=12)
        top_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            top_frame,
            text="VAULT HEIST: SAFE CRACKER",
            font=("Helvetica", 20, "bold"),
            anchor="w",
        )
        title_lbl.pack(fill=tk.X)

        purpose_lbl = tk.Label(
            top_frame,
            text=(
                "Objective: Lock all 3 vault dials inside their target ranges before Turns hit 0 or Heat hits 100%. "
                "Bigger spins move faster but risk pushing past the safe limit."
            ),
            font=("Helvetica", 10),
            fg="#334155",
            anchor="w",
            wraplength=720,
            justify="left",
        )
        purpose_lbl.pack(fill=tk.X, pady=(4, 8))

        stats_frame = tk.Frame(top_frame)
        stats_frame.pack(fill=tk.X)

        self.turns_lbl = tk.Label(stats_frame, text="", font=("Helvetica", 11, "bold"), fg="#1D4ED8")
        self.turns_lbl.pack(side=tk.LEFT, padx=(0, 20))

        self.heat_lbl = tk.Label(stats_frame, text="", font=("Helvetica", 11, "bold"), fg="#B91C1C")
        self.heat_lbl.pack(side=tk.LEFT, padx=(0, 20))

        self.score_lbl = tk.Label(stats_frame, text="", font=("Helvetica", 11, "bold"), fg="#0F766E")
        self.score_lbl.pack(side=tk.RIGHT)

        # Center 3-Dial Vault Panel
        dials_frame = tk.Frame(self.root, padx=16, pady=6)
        dials_frame.pack(fill=tk.BOTH, expand=True)

        self.dial_cards: list[tk.LabelFrame] = []
        self.dial_value_lbls: list[tk.Label] = []
        self.dial_info_lbls: list[tk.Label] = []

        for idx in range(3):
            card = tk.LabelFrame(
                dials_frame,
                text=f"Dial {idx + 1}",
                font=("Helvetica", 11, "bold"),
                padx=12,
                pady=12,
            )
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)

            val_lbl = tk.Label(card, text="0", font=("Helvetica", 28, "bold"))
            val_lbl.pack(pady=(12, 6))

            info_lbl = tk.Label(
                card,
                text="",
                font=("Helvetica", 10),
                justify="center",
                wraplength=190,
            )
            info_lbl.pack(pady=(4, 8))

            self.dial_cards.append(card)
            self.dial_value_lbls.append(val_lbl)
            self.dial_info_lbls.append(info_lbl)

        # Status Feed
        self.status_lbl = tk.Label(
            self.root,
            text="",
            font=("Helvetica", 10, "bold"),
            fg="#0F172A",
            wraplength=720,
            justify="center",
            pady=6,
        )
        self.status_lbl.pack(fill=tk.X, padx=16)

        # Bottom Button Bar (5 working buttons)
        btn_frame = tk.Frame(self.root, padx=16, pady=12)
        btn_frame.pack(fill=tk.X)

        self.spin_btn = tk.Button(
            btn_frame,
            text="Spin / Adjust",
            font=("Helvetica", 10, "bold"),
            padx=12,
            pady=6,
            command=self._on_spin,
        )
        self.spin_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.lock_btn = tk.Button(
            btn_frame,
            text="Lock Dial",
            font=("Helvetica", 10, "bold"),
            padx=12,
            pady=6,
            command=self._on_lock,
        )
        self.lock_btn.pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            btn_frame,
            text="New Heist",
            font=("Helvetica", 10, "bold"),
            padx=12,
            pady=6,
            command=self._on_new_heist,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            btn_frame,
            text="Credits",
            font=("Helvetica", 10),
            padx=12,
            pady=6,
            command=self._show_credits,
        ).pack(side=tk.RIGHT)

        tk.Button(
            btn_frame,
            text="Help",
            font=("Helvetica", 10),
            padx=12,
            pady=6,
            command=self._show_help,
        ).pack(side=tk.RIGHT, padx=(0, 8))

    def _on_spin(self) -> None:
        self.game.spin_active_dial()
        self._refresh_ui()

    def _on_lock(self) -> None:
        self.game.lock_active_dial()
        self._refresh_ui()

    def _on_new_heist(self) -> None:
        self.game.new_heist()
        self._refresh_ui()

    def _show_help(self) -> None:
        help_text = (
            "How to Play Vault Heist: Safe Cracker:\n\n"
            "1. Each round gives you 3 vault dials with a Target Range (e.g., 14-18).\n"
            "2. Click 'Spin / Adjust' to advance the active dial (-1 turn, +Heat).\n"
            "   - Pushing past the Safe Max value causes an extra Heat spike and pulls the dial back.\n"
            "3. Once the dial is inside its Target Range, click 'Lock Dial' (-1 turn) to secure it.\n"
            "4. Lock all 3 dials before Turns reach 0 or Heat reaches 100% to win!"
        )
        messagebox.showinfo("Help — Vault Heist", help_text)

    def _show_credits(self) -> None:
        credits_text = (
            "CMPS 5113 — Program 3 (Open-Ended OOP GUI)\n\n"
            "Game: Vault Heist: Safe Cracker\n"
            "Author: Harika Vemulapalli"
        )
        messagebox.showinfo("Credits", credits_text)

    def _refresh_ui(self) -> None:
        self.turns_lbl.config(text=f"Turns Left: {self.game.turns_left}")
        self.heat_lbl.config(text=f"Heat: {self.game.heat}% / {self.game.MAX_HEAT}%")
        self.score_lbl.config(text=f"Wins: {self.game.wins}  |  Losses: {self.game.losses}")
        self.status_lbl.config(text=self.game.status_message)

        for idx, dial in enumerate(self.game.dials):
            is_active = (idx == self.game.active_index) and not self.game.round_over
            if dial.locked:
                state_str = "LOCKED"
                bg_color = "#DCFCE7"
            elif is_active:
                state_str = "ACTIVE"
                bg_color = "#DBEAFE"
            else:
                state_str = "UNLOCKED"
                bg_color = "#F8FAFC"

            in_range_str = "In Target Range" if dial.is_in_target() else "Outside Target"

            self.dial_cards[idx].config(bg=bg_color)
            self.dial_value_lbls[idx].config(text=str(dial.value), bg=bg_color)
            self.dial_info_lbls[idx].config(
                text=(
                    f"State: {state_str}\n"
                    f"Target: {dial.target_min} - {dial.target_max}\n"
                    f"Safe Max: {dial.max_safe}\n"
                    f"({in_range_str})"
                ),
                bg=bg_color,
            )

        controls_enabled = not self.game.round_over
        self.spin_btn.config(state=tk.NORMAL if controls_enabled else tk.DISABLED)
        self.lock_btn.config(state=tk.NORMAL if controls_enabled else tk.DISABLED)


def main() -> None:
    root = tk.Tk()
    game = VaultHeistGame()
    VaultHeistGUI(root, game)
    root.mainloop()


if __name__ == "__main__":
    main()