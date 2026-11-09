# -*- coding: utf-8 -*-
"""
SAM LOC (SÂM LỐC - SUN.WIN) MATHEMATICAL AI BOT ENGINE & SIMULATOR
==================================================================
Hệ thống AI Sâm Lốc dựa trên Toán học Tổ hợp, Quy hoạch động (DP),
Xác suất Hypergeometric, Suy luận Bayes, Định lý Endgame 2-Combo
và Hệ thống Đánh giá Rủi ro XIN SÂM (Báo Sâm) theo % mạo hiểm (max_risk_percent).

Luật chuẩn Sâm Lốc SUN.WIN (cập nhật từ tài liệu & ảnh chụp màn hình trong game):
1. Bộ bài 52 lá, chia mỗi người 10 lá (từ 2 đến 5 người chơi).
2. Thứ tự độ lớn quân bài: 3 < 4 < 5 < 6 < 7 < 8 < 9 < 10 < J < Q < K < A < 2.
   - KHÔNG PHÂN BIỆT CHẤT (Cơ, Rô, Chuồn, Bích ngang nhau): Chỉ chặn được khi
     bộ bài cùng loại, cùng độ dài và có GIÁ TRỊ SỐ (Rank) lớn hơn hẳn.
3. Các bộ bài hợp lệ (SamComboType):
   - Bài lẻ (SINGLE): 1 lá. 2 là lớn nhất.
   - Đôi (PAIR): 2 lá cùng số. Đôi 2 lớn nhất.
   - Sám cô (TRIPLE): 3 lá cùng số. Sám 2 lớn nhất.
   - Tứ quý (FOUR_OF_KIND): 4 lá cùng số. Tứ quý 2 lớn nhất.
   - Sảnh (STRAIGHT): >= 3 lá liên tiếp, không phân biệt chất.
     * ĐẶC BIỆT SÂM LỐC: A và 2 được ghép sảnh nhỏ!
       Thứ tự độ lớn của Sảnh (cùng độ dài L):
       A-2-3-... < 2-3-4-... < 3-4-5-... < ... < J-Q-K < Q-K-A
       (Không có sảnh K-A-2).
4. Luật Chặt 2 (Chặt Heo):
   - Chỉ có TỨ QUÝ mới chặt được 2 (không có 3 đôi thông / 4 đôi thông chặt 2).
   - 1 Tứ quý chặt được 1 cây 2 lẻ (đền 10 lá/con 2 bị chặt).
   - 2 Tứ quý chặt được Đôi 2.
5. Luật Cấm Về Nhất Bằng 2 ("Thối 2 / Về bằng 2"):
   - Không được đánh quân 2 (lẻ, đôi 2, sám 2, tứ quý 2) ở nước bài CUỐI CÙNG để về nhất.
   - Nếu trên tay chỉ còn toàn 2 ở lượt cuối sẽ bị tính Thối 2 / Đền 15 lá.
6. Luật Báo 1 & Giữ Cửa:
   - Khi người chơi kế tiếp (ngồi ngay sau theo chiều đánh) chỉ còn 1 lá bài (Báo 1):
     + Nếu mở vòng (lead) bằng bài LẺ: Bắt buộc phải đánh cây lẻ CAO NHẤT đang có trên tay
       (hoặc phải chọn đánh bộ nhiều lá như Đôi, Sám, Sảnh).
     + Nếu đỡ bài LẺ trên bàn: Nếu có cây lẻ chặn được thì BẮT BUỘC phải chặn bằng cây lẻ
       CAO NHẤT trên tay. Nếu không chặn mà để người Báo 1 về nhất ngay lượt đó -> Đền 15 lá!
7. Luật BÁO SÂM (XIN SÂM):
   - Đầu ván (trước khi ai đánh lá đầu tiên), người chơi có thể bấm "Báo Sâm" (Xin Sâm).
   - Người Báo Sâm được giành quyền đánh trước và lần lượt đánh hết 10 lá bài trên tay.
   - Nếu từ đầu đến khi hết bài KHÔNG AI CHẶN ĐƯỢC nước nào (và nước cuối không phải là 2):
     -> Ăn Sâm thành công: Thắng mỗi nhà 20 lá (+20 * (N - 1) lá).
   - Nếu bị bất kỳ người chơi nào chặn được dù chỉ 1 nước:
     -> Ván bài dừng ngay lập tức, người Báo Sâm bị ĐỀN SÂM: Phạt 20 lá nhân số người chơi
        (-20 * (N - 1) lá trả cho người bắt được Sâm).
8. Cách tính thắng thua (Quy đổi theo đơn vị Lá = 1x tiền cược):
   - Thắng thường: Ăn số lá còn lại trên tay các nhà thua (1 lá = 1 cược).
   - Cóng (chưa đánh được lá nào): Phạt 15 lá + thối 2 (+10 lá/con) + thối Tứ quý (+10 lá/bộ).
   - Thối 2: Phạt 10 lá / 1 con 2.
   - Thối Tứ quý: Phạt 10 lá / 1 bộ Tứ quý.
"""

from __future__ import annotations
import itertools
import math
import random
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Sequence, Tuple

# ============================================================================
# 0. CẤU HÌNH LUẬT TÍNH TIỀN SÂM LỐC THEO CỔNG (SUN / HIT) — đơn vị: lá = 1 lần cược
# ============================================================================
@dataclass(frozen=True)
class SamRuleConfig:
    portal_name: str
    cong: int = 15                 # Thua cóng (chưa đánh lá nào)
    thoi_two: int = 10             # Mỗi con 2 còn trên tay khi thua
    thoi_four: int = 10            # Mỗi tứ quý còn trên tay khi thua
    chop_two: int = 10             # Bị tứ quý chặt 1 con 2
    finish_two_penalty: int = 15   # Về nhất bằng 2 (mỗi nhà)
    finish_two_allowed: bool = False  # SUN: cấm về bằng 2; HIT: được về nhưng bị tính thối 2
    bao_sam: int = 20              # Báo Sâm thắng/thua: x mỗi người còn lại
    an_trang: int = 20             # Ăn trắng: x mỗi người còn lại
    bao_mot_penalty: int = 15      # Không chặn người Báo 1 (HIT chưa ghi rõ mức -> tạm 15)


SAM_RULE_SUN = SamRuleConfig("SUN", finish_two_allowed=False)
SAM_RULE_HIT = SamRuleConfig("HIT", finish_two_allowed=True)
ACTIVE_SAM_RULE: SamRuleConfig = SAM_RULE_SUN


def set_sam_rule(portal: str) -> SamRuleConfig:
    global ACTIVE_SAM_RULE
    ACTIVE_SAM_RULE = SAM_RULE_HIT if str(portal).upper() == "HIT" else SAM_RULE_SUN
    return ACTIVE_SAM_RULE


# ============================================================================
# 1. BIỂU DIỄN LÁ BÀI & BỘ BÀI SÂM LỐC (KHÔNG PHÂN BIỆT CHẤT)
# ============================================================================

RANK_NAMES = ["3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A", "2"]
SUIT_NAMES = ["♠", "♣", "♦", "♥"]

RANK_3 = 0
RANK_4 = 1
RANK_5 = 2
RANK_6 = 3
RANK_7 = 4
RANK_8 = 5
RANK_9 = 6
RANK_10 = 7
RANK_J = 8
RANK_Q = 9
RANK_K = 10
RANK_A = 11
RANK_2 = 12


def card_rank(card_id: int) -> int:
    """Trả về rank của lá bài: 0 (3) -> 12 (2)."""
    return card_id // 4


def card_suit(card_id: int) -> int:
    """Trả về chất của lá bài: 0 (♠), 1 (♣), 2 (♦), 3 (♥). Lưu ý: Sâm Lốc không so chất."""
    return card_id % 4


def card_str(card_id: int) -> str:
    return f"{RANK_NAMES[card_rank(card_id)]}{SUIT_NAMES[card_suit(card_id)]}"


def hand_str(cards: Sequence[int]) -> str:
    return " ".join(card_str(c) for c in sorted(cards))


def parse_card(token: str) -> int:
    """Chuyển chuỗi bài (vd: '3♠', '10♥', 'A♦', '2♣' hoặc '3s', '10h') thành card_id (0..51)."""
    t = token.strip()
    suit_map = {
        "♠": 0, "s": 0, "S": 0, "b": 0,
        "♣": 1, "c": 1, "C": 1, "n": 1,
        "♦": 2, "d": 2, "D": 2, "r": 2,
        "♥": 3, "h": 3, "H": 3, "co": 3,
    }
    suit_char = t[-1]
    rank_part = t[:-1].upper()
    if suit_char not in suit_map:
        # Nếu chỉ truyền tên rank (vd 'A'), mặc định lấy chất Bích (0)
        rank_part = t.upper()
        suit_val = 0
    else:
        suit_val = suit_map[suit_char]
    rank_val = RANK_NAMES.index(rank_part)
    return rank_val * 4 + suit_val


class SamComboType(IntEnum):
    PASS = 0
    SINGLE = 1         # Bài lẻ (1 lá)
    PAIR = 2           # Đôi (2 lá cùng số)
    TRIPLE = 3         # Sám cô (3 lá cùng số)
    STRAIGHT = 4       # Sảnh (>= 3 lá liên tiếp, gồm cả A-2-3 và 2-3-4)
    FOUR_OF_KIND = 5   # Tứ quý (4 lá cùng số - chặt được 1 cây 2)


@dataclass(frozen=True)
class SamCombo:
    combo_type: SamComboType
    cards: Tuple[int, ...]
    length: int          # Số lượng lá bài trong bộ (3..10 cho Sảnh, 1..4 cho bộ cùng số)
    order_value: int     # Giá trị so sánh độ lớn (trong Sâm Lốc CHỈ phụ thuộc vào số, KHÔNG phụ thuộc chất!)
    label: str = ""      # Mô tả ngắn (vd: "Sảnh A-2-3", "Sảnh 2-3-4", "Đôi K")

    @property
    def is_pass(self) -> bool:
        return self.combo_type == SamComboType.PASS

    @property
    def is_all_twos(self) -> bool:
        """Kiểm tra bộ bài có phải toàn quân 2 hay không (Cấm đánh ở nước cuối về nhất)."""
        return (
            not self.is_pass
            and self.combo_type in (
                SamComboType.SINGLE,
                SamComboType.PAIR,
                SamComboType.TRIPLE,
                SamComboType.FOUR_OF_KIND,
            )
            and self.order_value == RANK_2
        )

    @property
    def contains_two(self) -> bool:
        return any(card_rank(c) == RANK_2 for c in self.cards)

    def __repr__(self) -> str:
        if self.is_pass:
            return "PASS"
        if self.label:
            return f"{self.label}({hand_str(self.cards)})"
        return f"{self.combo_type.name}({hand_str(self.cards)})"


PASS_COMBO = SamCombo(SamComboType.PASS, (), 0, -1, "PASS")


# ============================================================================
# 2. LUẬT SO SÁNH & SINH NƯỚC ĐI HỢP LỆ TRONG SÂM LỐC
# ============================================================================
# Thứ tự Sảnh cùng độ dài L >= 3 trong Sâm Lốc:
#   - Sảnh A-2-3-...-(L):          order_value = 0 (nhỏ nhất: bắt đầu từ A, kế tiếp là 2, 3, ...)
#   - Sảnh 2-3-4-...-(L+1):        order_value = 1 (nhỏ nhì: bắt đầu từ 2, kế tiếp là 3, 4, ...)
#   - Sảnh thường bắt đầu từ r:    order_value = r + 2 (với r = 0 (quân 3) .. 12 - L (tối đa tới A))
# Như vậy với sảnh 3 lá:
#   A-2-3 (order=0) < 2-3-4 (order=1) < 3-4-5 (order=2) < ... < J-Q-K (order=10) < Q-K-A (order=11).
# Hoàn toàn khớp 100% với quy tắc Sâm Lốc SUN: "A23 < 234 < 345 < ... < JQK < QKA"!


def straight_max_order_value(length: int) -> int:
    """Giá trị order_value lớn nhất của một Sảnh có độ dài `length` (tức sảnh kết thúc tại A)."""
    # Sảnh kết thúc tại A (rank 11) có rank bắt đầu là r = 12 - length -> order_value = 14 - length
    return 14 - length


def can_beat_sam(prev: Optional[SamCombo], cand: SamCombo) -> bool:
    """
    Kiểm tra bộ `cand` có chặt/đè được bộ `prev` theo đúng luật Sâm Lốc SUN không.
    - Không phân biệt chất: `cand.order_value > prev.order_value`.
    - Tứ quý chặt được 2 lẻ (1 Tứ quý chặt 1 cây 2).
    """
    if cand.is_pass:
        return False
    if prev is None or prev.is_pass:
        return True

    # 1. Cùng loại bộ và cùng số lá -> chỉ so sánh order_value (KHÔNG so chất)
    if cand.combo_type == prev.combo_type and cand.length == prev.length:
        return cand.order_value > prev.order_value

    # 2. Luật Chặt 2 (Heo) trong Sâm Lốc: 1 Tứ quý chặt được 1 cây 2 lẻ
    if prev.combo_type == SamComboType.SINGLE and prev.order_value == RANK_2:
        if cand.combo_type == SamComboType.FOUR_OF_KIND:
            return True

    return False


def generate_all_sam_combos(hand: Sequence[int]) -> List[SamCombo]:
    """
    Sinh toàn bộ các bộ bài hợp lệ từ tập bài `hand` theo luật Sâm Lốc (gồm cả Sảnh A-2-3 và 2-3-4).
    """
    sorted_hand = sorted(hand)
    by_rank: Dict[int, List[int]] = {}
    for c in sorted_hand:
        by_rank.setdefault(card_rank(c), []).append(c)

    combos: List[SamCombo] = []

    # 1. Bài lẻ (SINGLE)
    for c in sorted_hand:
        r = card_rank(c)
        combos.append(SamCombo(SamComboType.SINGLE, (c,), 1, r, f"Lẻ {RANK_NAMES[r]}"))

    # 2. Đôi (PAIR), Sám cô (TRIPLE), Tứ quý (FOUR_OF_KIND)
    for r, cards in sorted(by_rank.items()):
        n = len(cards)
        if n >= 2:
            for pair in itertools.combinations(cards, 2):
                combos.append(SamCombo(SamComboType.PAIR, pair, 2, r, f"Đôi {RANK_NAMES[r]}"))
        if n >= 3:
            for trip in itertools.combinations(cards, 3):
                combos.append(SamCombo(SamComboType.TRIPLE, trip, 3, r, f"Sám {RANK_NAMES[r]}"))
        if n == 4:
            combos.append(SamCombo(SamComboType.FOUR_OF_KIND, tuple(cards), 4, r, f"Tứ quý {RANK_NAMES[r]}"))

    # 3. Sảnh thường (từ 3 đến A, tức rank 0..11)
    normal_ranks = sorted(r for r in by_rank if r < RANK_2)
    num_nr = len(normal_ranks)
    i = 0
    while i < num_nr:
        j = i
        while j + 1 < num_nr and normal_ranks[j + 1] == normal_ranks[j] + 1:
            j += 1
        run_len = j - i + 1
        if run_len >= 3:
            for start_idx in range(i, j - 1):
                for end_idx in range(start_idx + 2, j + 1):
                    seq_ranks = normal_ranks[start_idx : end_idx + 1]
                    L = len(seq_ranks)
                    start_r = seq_ranks[0]
                    end_r = seq_ranks[-1]
                    order_val = start_r + 2
                    label = f"Sảnh {RANK_NAMES[start_r]}-{RANK_NAMES[end_r]}"
                    # Trong Sâm Lốc không phân biệt chất, nếu có nhiều lá cùng số trong sảnh,
                    # để tránh bùng nổ tổ hợp khi 10 lá có đôi xen kẽ, ta lấy đại diện (hoặc tối đa 2 biến thể)
                    card_pools = [by_rank[r][:2] for r in seq_ranks]
                    for prod in itertools.product(*card_pools):
                        combos.append(
                            SamCombo(SamComboType.STRAIGHT, tuple(sorted(prod)), L, order_val, label)
                        )
        i = j + 1

    # 4. Sảnh đặc biệt Sâm Lốc:
    # 4a. Sảnh A-2-3-... (bắt đầu từ A, 2, rồi nối tiếp 3, 4, 5, ... tối đa tới K để không lặp A)
    if RANK_A in by_rank and RANK_2 in by_rank and RANK_3 in by_rank:
        # Tìm chuỗi liên tiếp bắt đầu từ 3 (rank 0) tới tối đa K (rank 10)
        max_low_r = RANK_3
        while (max_low_r + 1) <= RANK_K and (max_low_r + 1) in by_rank:
            max_low_r += 1
        # Độ dài phần từ 3 trở đi: từ 1 lá (chỉ có 3 -> sảnh A-2-3) đến hết chuỗi
        for end_r in range(RANK_3, max_low_r + 1):
            seq_ranks = [RANK_A, RANK_2] + list(range(RANK_3, end_r + 1))
            L = len(seq_ranks)
            label = f"Sảnh A-2-{RANK_NAMES[end_r]}"
            card_pools = [by_rank[r][:1] for r in seq_ranks]
            for prod in itertools.product(*card_pools):
                combos.append(
                    SamCombo(SamComboType.STRAIGHT, tuple(sorted(prod)), L, 0, label)
                )

    # 4b. Sảnh 2-3-4-... (bắt đầu từ 2, rồi nối tiếp 3, 4, ... tối đa tới A)
    if RANK_2 in by_rank and RANK_3 in by_rank and RANK_4 in by_rank:
        max_low_r = RANK_4
        while (max_low_r + 1) <= RANK_A and (max_low_r + 1) in by_rank:
            max_low_r += 1
        for end_r in range(RANK_4, max_low_r + 1):
            seq_ranks = [RANK_2] + list(range(RANK_3, end_r + 1))
            L = len(seq_ranks)
            label = f"Sảnh 2-3-{RANK_NAMES[end_r]}"
            card_pools = [by_rank[r][:1] for r in seq_ranks]
            for prod in itertools.product(*card_pools):
                combos.append(
                    SamCombo(SamComboType.STRAIGHT, tuple(sorted(prod)), L, 1, label)
                )

    return combos


def classify_sam_cards(cards: Sequence[int]) -> Optional[SamCombo]:
    """
    Nhận diện bộ bài Sâm Lốc (`SamCombo`) từ danh sách các lá bài vừa đánh ra trên bàn (`dCs`).
    """
    if not cards:
        return None
    target_len = len(cards)
    matches = [c for c in generate_all_sam_combos(cards) if c.length == target_len]
    if not matches:
        return None
    # Nếu có nhiều cách hiểu (hiếm gặp), ưu tiên loại bộ mạnh hơn và order_value cao hơn
    matches.sort(key=lambda c: (int(c.combo_type), c.order_value), reverse=True)
    return matches[0]


def would_leave_only_twos(hand: Sequence[int], move: SamCombo) -> bool:
    """
    Kiểm tra nếu đánh nước `move` thì số bài còn lại trên tay có bị rơi vào trạng thái:
    - Hết bài ngay bằng quân 2 (`move.is_all_twos` khi `len(hand) == move.length`), HOẶC
    - Các lá còn lại trên tay toàn bộ là quân 2 (chắc chắn sẽ bị Thối 2 / Về bằng 2 ở nước sau!).
    """
    if move.is_pass:
        return False
    rem = [c for c in hand if c not in move.cards]
    if not rem:
        # Đánh hết bài ngay trong nước này: nếu nước này là 2 (lẻ/đôi/sám/tứ quý 2) -> CẤM!
        return move.is_all_twos
    # Nếu còn bài trên tay mà tất cả các lá còn lại đều là quân 2 -> Chết kẹt Thối 2!
    if all(card_rank(c) == RANK_2 for c in rem):
        return True
    return False


def get_legal_sam_moves(
    hand: Sequence[int],
    board_combo: Optional[SamCombo] = None,
    next_player_card_count: int = 10,
    strict_bao_mot: bool = True,
) -> List[SamCombo]:
    """
    Lấy danh sách toàn bộ các nước đi hợp lệ trong Sâm Lốc, đã áp dụng:
    1. Luật không được về nhất bằng 2 (không cho phép đánh bộ toàn 2 làm nước kết thúc).
    2. Luật Giữ Cửa khi nhà kế tiếp Báo 1 (`next_player_card_count == 1`):
       - Nếu mở vòng (board_combo is None): Nếu đánh bài LẺ thì chỉ được phép đánh cây lẻ CAO NHẤT
         trên tay (các bộ Đôi/Sám/Sảnh/Tứ quý vẫn được đánh bình thường).
       - Nếu đỡ bài LẺ trên bàn (`board_combo.combo_type == SINGLE`): Nếu có cây lẻ chặn được
         thì BẮT BUỘC phải chặn bằng cây lẻ CAO NHẤT (hoặc chặt 2 bằng Tứ quý), KHÔNG ĐƯỢC PASS!
    """
    all_combos = generate_all_sam_combos(hand)
    hand_len = len(hand)

    # Lọc bỏ nước đi làm cho lượt cuối về nhất bằng 2
    valid_combos = [
        c for c in all_combos
        if not (len(c.cards) == hand_len and c.is_all_twos)
    ]

    if board_combo is None or board_combo.is_pass:
        # MỞ VÒNG (Lead)
        if not valid_combos and all_combos:
            # Trên tay chỉ còn toàn 2 mà phải mở vòng: bắt buộc đánh (SUN xử phạt / HIT tính thối 2)
            valid_combos = list(all_combos)
        if strict_bao_mot and next_player_card_count == 1 and valid_combos:
            singles = [c for c in valid_combos if c.combo_type == SamComboType.SINGLE]
            if singles:
                max_single_rank = max(c.order_value for c in singles)
                # Chỉ giữ lại các cây lẻ có rank == max_single_rank và mọi bộ >= 2 lá
                filtered = [
                    c for c in valid_combos
                    if c.combo_type != SamComboType.SINGLE or c.order_value == max_single_rank
                ]
                if filtered:
                    return filtered
        return valid_combos

    # ĐỠ BÀI TRÊN BÀN (Respond)
    beating = [c for c in valid_combos if can_beat_sam(board_combo, c)]

    if strict_bao_mot and next_player_card_count == 1 and board_combo.combo_type == SamComboType.SINGLE:
        # Nhà dưới Báo 1 và bài trên bàn là LẺ:
        # Nếu có khả năng chặn (bằng lẻ lớn hơn hoặc Tứ quý chặt 2), BẮT BUỘC phải chặn bằng cây cao nhất!
        if beating:
            beating_singles = [c for c in beating if c.combo_type == SamComboType.SINGLE]
            beating_bombs = [c for c in beating if c.combo_type == SamComboType.FOUR_OF_KIND]
            if beating_singles:
                max_s_rank = max(c.order_value for c in beating_singles)
                highest_singles = [c for c in beating_singles if c.order_value == max_s_rank]
                return highest_singles + beating_bombs
            return beating_bombs

    beating.append(PASS_COMBO)
    return beating


# ============================================================================
# 3. QUY HOẠCH ĐỘNG (DP) PHÂN RÃ BÀI SÂM LỐC TỐI ƯU (10 LÁ)
# ============================================================================

@dataclass
class SamPartitionPlan:
    combos: List[SamCombo]
    num_turns: int
    free_turns: float       # Số lượt thực sự phải tốn quyền điều bài (trừ các bộ Boss/Cực mạnh)
    trash_count: int        # Số bài lẻ rác (< J)
    boss_count: int         # Số bộ/quân bài cực đại (2, Sảnh thượng, Tứ quý)
    only_twos_end_risk: bool  # Cảnh báo nếu phân rã này có nguy cơ kẹt 2 cuối bài
    total_score: float      # Điểm đánh giá tổng hợp của thế bài (càng cao càng mạnh)


def is_boss_sam_combo(combo: SamCombo, unseen_cards: Optional[Sequence[int]] = None) -> bool:
    """
    Kiểm tra xem `combo` có phải là bộ BẤT BẠI (hoặc gần như bất bại) trên bàn Sâm Lốc không.
    """
    if combo.is_pass:
        return False
    if unseen_cards is None:
        # Đánh giá tĩnh đầu ván:
        if combo.combo_type == SamComboType.FOUR_OF_KIND:
            return True
        if combo.combo_type in (SamComboType.SINGLE, SamComboType.PAIR, SamComboType.TRIPLE):
            return combo.order_value == RANK_2
        if combo.combo_type == SamComboType.STRAIGHT:
            # Sảnh kết thúc tại A hoặc K hoặc sảnh dài >= 5 lá
            max_ord = straight_max_order_value(combo.length)
            return combo.order_value >= max_ord - 1 or combo.length >= 6
        return False

    # Đánh giá động dựa trên các lá bài chưa lộ (`unseen_cards`):
    unseen_ranks = Counter(card_rank(c) for c in unseen_cards)
    if combo.combo_type == SamComboType.SINGLE:
        if combo.order_value == RANK_2:
            # Trong Sâm Lốc, quân 2 luôn là Boss kiểm soát vòng đơn (không quân 2 nào đè được 2)
            return True
        return all(r <= combo.order_value for r in unseen_ranks)
    if combo.combo_type == SamComboType.PAIR:
        return not any(r > combo.order_value and cnt >= 2 for r, cnt in unseen_ranks.items())
    if combo.combo_type == SamComboType.TRIPLE:
        return not any(r > combo.order_value and cnt >= 3 for r, cnt in unseen_ranks.items())
    if combo.combo_type == SamComboType.FOUR_OF_KIND:
        return not any(r > combo.order_value and cnt == 4 for r, cnt in unseen_ranks.items())
    if combo.combo_type == SamComboType.STRAIGHT:
        L = combo.length
        max_ord = straight_max_order_value(L)
        for cand_ord in range(combo.order_value + 1, max_ord + 1):
            # cand_ord >= 2 tương ứng sảnh thường bắt đầu từ start_r = cand_ord - 2
            if cand_ord == 1:
                req = [RANK_2] + list(range(RANK_3, RANK_3 + L - 1))
            else:
                start_r = cand_ord - 2
                req = list(range(start_r, start_r + L))
            if all(unseen_ranks[r] >= 1 for r in req):
                return False
        return True
    return False


def _extract_sam_opp_pass_caps(state: "SamTableState") -> Dict[str, Any]:
    """
    [V5.0 LIVE SITUATION READER - SÂM LỐC]
    Đọc tình huống động giữa trận & cuối trận từ lịch sử bỏ lượt `state.opp_pass_log`:
    Mỗi khi đối thủ đánh ra hoặc bỏ lượt (pass), cập nhật trần bài của từng đối thủ còn bài:
    - `single_cap`: Đối thủ đã bỏ lượt trước Lẻ `r` -> xác suất đối thủ giữ Lẻ > `r` giảm mạnh.
    - `opp_no_two`: Đối thủ đã bỏ lượt trước `Lẻ A` (hoặc `Lẻ K` khi còn <= 6 lá và chưa đánh 2 sau đó)
      -> đối thủ gần như chắc chắn KHÔNG CẦM HEO (2 nằm trong 32 lá bài úp dưới nọc!).
    - `pair_cap`, `triple_cap`, `straight_cap[L]`: Trần Đôi, Sám, Sảnh độ dài L của đối thủ.
    """
    active_opps = [
        s for s in range(state.num_players)
        if s != state.my_seat and state.cards_left[s] > 0
    ]
    per_opp: Dict[int, Dict[str, Any]] = {
        s: {
            "single_cap": 99,
            "opp_no_two": False,
            "pair_cap": 99,
            "triple_cap": 99,
            "straight_cap": {},
            "pass_count": 0,
        }
        for s in active_opps
    }
    raw_log = getattr(state, "opp_pass_log", None) or {}
    for s in active_opps:
        entries = raw_log.get(s) or []
        info = per_opp[s]
        info["pass_count"] = len(entries)
        opp_cards = state.cards_left[s]
        for bc, played_after in entries:
            if bc is None or bc.is_pass:
                continue
            played_two_after = any(card_rank(c) == RANK_2 for c in (played_after or ()))
            if bc.combo_type == SamComboType.SINGLE and not bc.is_all_twos:
                if opp_cards <= 6 or bc.order_value >= RANK_Q:
                    if bc.order_value < info["single_cap"]:
                        info["single_cap"] = bc.order_value
                if bc.order_value == RANK_A and not played_two_after:
                    info["opp_no_two"] = True
                elif bc.order_value == RANK_K and opp_cards <= 6 and not played_two_after:
                    info["opp_no_two"] = True
            elif bc.combo_type == SamComboType.PAIR and not bc.is_all_twos:
                if bc.order_value < info["pair_cap"]:
                    info["pair_cap"] = bc.order_value
            elif bc.combo_type == SamComboType.TRIPLE and not bc.is_all_twos:
                if bc.order_value < info["triple_cap"]:
                    info["triple_cap"] = bc.order_value
            elif bc.combo_type == SamComboType.STRAIGHT:
                L = bc.length
                cur_sc = info["straight_cap"].get(L, 99)
                if bc.order_value < cur_sc:
                    info["straight_cap"][L] = bc.order_value

    all_opps_no_two = bool(active_opps) and all(per_opp[s]["opp_no_two"] for s in active_opps)
    max_single_cap = max((per_opp[s]["single_cap"] for s in active_opps), default=99)
    max_pair_cap = max((per_opp[s]["pair_cap"] for s in active_opps), default=99)
    max_triple_cap = max((per_opp[s]["triple_cap"] for s in active_opps), default=99)
    max_straight_cap: Dict[int, int] = {}
    all_st_lens = {L for s in active_opps for L in per_opp[s]["straight_cap"]}
    for L in all_st_lens:
        max_straight_cap[L] = max(per_opp[s]["straight_cap"].get(L, 99) for s in active_opps)
    min_pass_count = min((per_opp[s]["pass_count"] for s in active_opps), default=0)

    return {
        "per_opp": per_opp,
        "all_opps_no_two": all_opps_no_two,
        "max_single_cap": max_single_cap,
        "max_pair_cap": max_pair_cap,
        "max_triple_cap": max_triple_cap,
        "max_straight_cap": max_straight_cap,
        "min_pass_count": min_pass_count,
    }


def _is_effective_boss_sam_combo(
    combo: SamCombo,
    unseen_cards: Optional[Sequence[int]] = None,
    pass_caps: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Kiểm tra xem `combo` có phải là Bộ Bất Bại Thực Tế (Effective Boss) trên bàn Sâm Lốc:
    Hoặc bất bại tuyệt đối theo bài chưa lộ (`is_boss_sam_combo`), hoặc mọi đối thủ còn bài
    đều đã BỎ LƯỢT trước một bộ cùng loại nhỏ hơn/bằng `combo`!
    """
    if is_boss_sam_combo(combo, unseen_cards):
        return True
    if not pass_caps or not pass_caps.get("per_opp"):
        return False
    if combo.combo_type == SamComboType.SINGLE:
        if combo.order_value == RANK_A and pass_caps.get("all_opps_no_two"):
            return True
        if combo.order_value >= pass_caps.get("max_single_cap", 99) and pass_caps.get("all_opps_no_two"):
            return True
    elif combo.combo_type == SamComboType.PAIR:
        if combo.order_value >= pass_caps.get("max_pair_cap", 99):
            unseen_twos = (
                sum(1 for c in unseen_cards if card_rank(c) == RANK_2)
                if unseen_cards is not None
                else 4
            )
            if unseen_twos < 2 or pass_caps.get("all_opps_no_two") or combo.order_value >= RANK_8:
                return True
    elif combo.combo_type == SamComboType.TRIPLE:
        if combo.order_value >= pass_caps.get("max_triple_cap", 99):
            return True
    elif combo.combo_type == SamComboType.STRAIGHT:
        if combo.order_value >= pass_caps.get("max_straight_cap", {}).get(combo.length, 99):
            return True
    return False


def optimal_partition_sam_hand(
    hand: Sequence[int],
    unseen_cards: Optional[Sequence[int]] = None,
) -> SamPartitionPlan:
    """
    Quy hoạch động (Branch & Bound trên 10 lá bài) tìm cách xếp bài Sâm Lốc tối ưu nhất:
    - Tối thiểu hóa số lượt đi (`num_turns`) và số lượt rỗng (`free_turns`).
    - Tự động cân nhắc việc ghép quân `2` vào sảnh `A-2-3` / `2-3-4`:
      + Nếu ghép `2` vào sảnh giúp giảm mạnh số rác lẻ (vd cứu được 3-4 hay A-3 lẻ) HOẶC giúp
        tránh bị kẹt toàn 2 ở cuối bài -> ghép `2` vào sảnh.
      + Ngược lại nếu `2` đứng riêng làm quân chủ bài kiểm soát vòng tốt hơn -> giữ `2`.
    """
    sorted_hand = tuple(sorted(hand))
    if not sorted_hand:
        return SamPartitionPlan([], 0, 0.0, 0, 0, False, 100.0)

    all_combos = generate_all_sam_combos(sorted_hand)
    # Nhóm các bộ 다 lá (>= 2 lá) theo tập bài để tránh xét trùng biến thể chất trong cùng tập bài
    multi_combos_by_cardset: Dict[Tuple[int, ...], SamCombo] = {}
    for c in all_combos:
        if c.length >= 2:
            multi_combos_by_cardset[c.cards] = c
    multi_combos = list(multi_combos_by_cardset.values())
    # Ưu tiên duyệt bộ dài trước (Sảnh dài, Tứ quý, Sám, Đôi)
    multi_combos.sort(key=lambda c: (-c.length, - int(c.combo_type), -c.order_value))

    best_plan: Optional[SamPartitionPlan] = None

    def evaluate_combo_list(chosen_multis: List[SamCombo], leftover_cards: List[int]) -> SamPartitionPlan:
        full_list = list(chosen_multis)
        for c in leftover_cards:
            r = card_rank(c)
            full_list.append(SamCombo(SamComboType.SINGLE, (c,), 1, r, f"Lẻ {RANK_NAMES[r]}"))

        num_turns = len(full_list)
        trash_count = 0
        non2_singles_count = 0
        boss_count = 0
        power_bonus = 0.0

        non_two_combos = [cb for cb in full_list if not cb.is_all_twos]
        only_twos_end_risk = (len(non_two_combos) == 0)

        for cb in full_list:
            is_boss = is_boss_sam_combo(cb, unseen_cards)
            if is_boss:
                boss_count += 1

            if cb.combo_type == SamComboType.SINGLE:
                if cb.order_value < RANK_A:
                    non2_singles_count += 1
                if cb.order_value < RANK_J:
                    trash_count += 1
                    power_bonus -= (RANK_J - cb.order_value) * 0.45
                elif cb.order_value == RANK_2:
                    power_bonus += 5.5
                elif cb.order_value == RANK_A:
                    power_bonus += 2.8
                elif cb.order_value == RANK_K:
                    power_bonus += 1.4
                else:
                    power_bonus += 0.5
            elif cb.combo_type == SamComboType.PAIR:
                if cb.order_value == RANK_2:
                    power_bonus += 8.0
                elif cb.order_value >= RANK_Q:
                    power_bonus += 3.5 + (cb.order_value - RANK_Q) * 1.1
                else:
                    power_bonus += 2.2 + cb.order_value * 0.22
            elif cb.combo_type == SamComboType.TRIPLE:
                power_bonus += 6.8 + cb.order_value * 0.45
            elif cb.combo_type == SamComboType.FOUR_OF_KIND:
                power_bonus += 14.0 + cb.order_value * 0.5
            elif cb.combo_type == SamComboType.STRAIGHT:
                max_ord = straight_max_order_value(cb.length)
                rel_strength = cb.order_value / max(1, max_ord)
                if cb.order_value == 0:
                    # Sảnh A-2-3...: order_value = 0 (nhỏ nhất mọi sảnh, không thể dùng để đỡ bất kỳ sảnh nào)
                    # và tiêu tốn cả A lẫn 2 (2 quân chủ lực bắt bài lẻ để cướp cái).
                    # Đặc biệt với độ dài >= 5 (A-2-3-4-5...), phần 3-4-5... vốn đã là sảnh hợp lệ, ghép thêm A-2 chỉ làm mất không A và 2!
                    if num_turns == 1:
                        power_bonus += 32.0
                    else:
                        if cb.length == 3:
                            trash_count += 1
                            power_bonus -= 28.0
                        elif cb.length == 4 and num_turns <= 5:
                            trash_count += 1
                            power_bonus -= 22.0
                        else:
                            trash_count += 2
                            power_bonus -= 44.0
                elif cb.order_value == 1:
                    # Sảnh 2-3-4...: order_value = 1 (chỉ ăn được A-2-3) và tiêu tốn quân 2.
                    # Với độ dài >= 4 (2-3-4-5...), phần 3-4-5... vốn đã là sảnh hợp lệ, ghép thêm 2 chỉ làm mất không Heo!
                    if num_turns == 1:
                        power_bonus += 32.0
                    else:
                        if cb.length == 3:
                            trash_count += 1
                            power_bonus -= 40.0
                        else:
                            trash_count += 1
                            power_bonus -= 36.0
                else:
                    power_bonus += 3.2 + cb.length * 1.35 + rel_strength * 3.5 + (max(0, cb.length - 4) * 8.5)

        free_turns = max(0.0, float(num_turns - boss_count - 1))
        total_score = (
            100.0
            - num_turns * 9.5
            - free_turns * 5.0
            - trash_count * 3.8
            - non2_singles_count * 3.5
            + power_bonus
            - (40.0 if only_twos_end_risk else 0.0)
        )
        return SamPartitionPlan(
            combos=full_list,
            num_turns=num_turns,
            free_turns=free_turns,
            trash_count=trash_count,
            boss_count=boss_count,
            only_twos_end_risk=only_twos_end_risk,
            total_score=total_score,
        )

    # Vì bài Sâm chỉ có tối đa 10 lá, đệ quy quay lui trên các bộ >= 2 lá cực kỳ nhanh (< 0.2ms)
    def dfs(idx: int, used_mask: int, chosen: List[SamCombo]) -> None:
        nonlocal best_plan
        leftover = [sorted_hand[k] for k in range(len(sorted_hand)) if not (used_mask & (1 << k))]
        cand_plan = evaluate_combo_list(chosen, leftover)
        if best_plan is None or cand_plan.total_score > best_plan.total_score:
            best_plan = cand_plan

        if not leftover or len(leftover) < 2:
            return

        for m_idx in range(idx, len(multi_combos)):
            mc = multi_combos[m_idx]
            if mc.length > len(leftover):
                continue
            # Kiểm tra các lá của mc có nằm trong phần chưa dùng không
            m_mask = 0
            possible = True
            for card in mc.cards:
                pos = sorted_hand.index(card)
                if used_mask & (1 << pos):
                    possible = False
                    break
                m_mask |= (1 << pos)
            if possible:
                chosen.append(mc)
                dfs(m_idx + 1, used_mask | m_mask, chosen)
                chosen.pop()

    dfs(0, 0, [])
    assert best_plan is not None
    return best_plan


# ============================================================================
# 4. CÔNG THỨC TOÁN HỌC & BỘ ĐÁNH GIÁ "XIN SÂM" (BÁO SÂM) THEO % MẠO HIỂM
# ============================================================================
# Bài toán Toán học Xin Sâm:
# --------------------------
# Giả sử người chơi có 10 lá bài H, bàn chơi có N người (tức có N - 1 đối thủ,
# mỗi đối thủ cầm 10 lá lấy ngẫu nhiên từ 42 lá bài chưa biết U = Deck \ H).
#
# Khi tuyên bố "Xin Sâm" (Báo Sâm), người chơi phải đánh một chuỗi phân hoạch hợp lệ:
#     pi = (m_1, m_2, ..., m_k)   với U_{j=1..k} m_j = H
# sao cho:
#   1. Nước cuối cùng m_k KHÔNG PHẢI là quân 2 / đôi 2 / sám 2 / tứ quý 2 (`not m_k.is_all_twos`).
#   2. Mọi nước dẫn đường từ m_1 đến m_{k-1} KHÔNG BỊ BẤT KỲ ĐỐI THỦ NÀO CHẶN!
#      (Khi m_1 .. m_{k-1} đều không ai chặn được, người chơi vẫn giữ cái ở nước cuối m_k
#       và đặt nốt bộ hợp lệ m_k xuống bàn là HẾT BÀI -> Thắng Sâm ngay lập tức!).
#      * Lưu ý an toàn: Cả trường hợp một số cổng xét thêm xác suất m_k bị bắt nếu m_k quá nhỏ
#        khi còn nhiều nhịp cũng được tính trọng số an toàn `tail_exposure_weight` để đảm bảo
#        xác suất thực nghiệm khớp chuẩn xác với ngưỡng mạo hiểm!
#
# Xác suất thành công của chuỗi đánh pi:
#     P(Sâm thành công | pi) = P(Không đối thủ nào trong N-1 nhà chặn được m_1, ..., m_{k-1})
#
# Độ mạo hiểm (Rủi ro bị bắt đền Sâm):
#     Risk(pi) = (1 - P(Sâm thành công | pi)) * 100%
#
# Kỳ vọng lợi ích (Expected Value - tính theo đơn vị Lá cược):
#     EV(pi) = P_win * [20 * (N - 1)] - (1 - P_win) * [20 * (N - 1)]
#            = 20 * (N - 1) * (2 * P_win - 1)
#
# Quyết định Xin Sâm với tham số đầu vào `max_risk_percent` (0% -> 100%):
#     - Chọn chuỗi đánh pi* cực tiểu hóa Risk(pi).
#     - Cho phép Xin Sâm khi và chỉ khi:
#           Risk(pi*) <= max_risk_percent


@dataclass
class XinSamAnalysis:
    should_declare: bool             # Quyết định có Xin Sâm hay không ứng với max_risk_percent
    win_probability: float           # Xác suất ăn Sâm thành công (0.0 -> 1.0)
    risk_percent: float              # % Rủi ro bị bắt đền Sâm = (1 - win_probability) * 100
    max_risk_percent: float          # Ngưỡng % mạo hiểm tối đa được truyền vào
    expected_value_cards: float      # Kỳ vọng số lá thắng/thua: EV = 20*(N-1)*(2*P_win - 1)
    planned_sequence: List[SamCombo] # Thứ tự đánh các bộ bài từ đầu đến cuối khi Xin Sâm
    step_risks: List[Tuple[SamCombo, float]]  # Rủi ro bị chặn của từng nước đi trong chuỗi
    reason: str                      # Giải thích chi tiết bằng tiếng Việt


def _analytic_single_move_beaten_prob(
    move: SamCombo,
    unseen_ranks: Counter,
    num_opponents: int,
    opp_hand_size: int = 10,
    pass_caps: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Tính xấp xỉ Giải tích Tổ hợp (Hypergeometric) xác suất ít nhất 1 trong `num_opponents`
    đối thủ (mỗi người `opp_hand_size` lá từ tập bài chưa lộ `unseen_ranks`) có bộ bài chặn được `move`.
    Dùng để sắp xếp thứ tự ưu tiên các bộ bài trong chuỗi Xin Sâm và đánh giá xác suất thu hồi cái giữa ván:
    - Các bộ có xác suất bị chặn thấp nhất (0% hoặc gần 0%) được đánh TRƯỚC (m_1 .. m_{k-1}).
    - Bộ yếu nhất (nhưng không phải quân 2) được đẩy xuống làm nước KẾT THÚC (m_k).
    """
    total_unseen = sum(unseen_ranks.values())
    draw_k = min(max(1, opp_hand_size), total_unseen)
    if total_unseen == 0 or num_opponents <= 0 or draw_k <= 0:
        return 0.0
    total_ways = math.comb(total_unseen, draw_k)
    if total_ways == 0:
        return 0.0

    # 1. Bài LẺ (SINGLE)
    if move.combo_type == SamComboType.SINGLE:
        if move.order_value == RANK_2:
            if draw_k < 4 or total_unseen < 4:
                return 0.0
            # Cây 2 lẻ chỉ bị chặt bởi Tứ quý (cần cả 4 lá cùng rank nằm trong tay 1 đối thủ)
            quad_ranks = [r for r, cnt in unseen_ranks.items() if cnt == 4]
            if not quad_ranks:
                return 0.0
            p_one_opp_one_quad = math.comb(total_unseen - 4, draw_k - 4) / total_ways
            return min(1.0, len(quad_ranks) * num_opponents * p_one_opp_one_quad)

        all_no_two = bool(pass_caps and pass_caps.get("all_opps_no_two"))
        higher_cards = sum(
            cnt for r, cnt in unseen_ranks.items()
            if r > move.order_value and not (all_no_two and r == RANK_2)
        )
        if higher_cards == 0:
            return 0.0
        opp_total_cards = min(total_unseen, draw_k * num_opponents)
        if total_unseen - higher_cards < opp_total_cards:
            p_beat = 1.0
        else:
            p_none = math.comb(total_unseen - higher_cards, opp_total_cards) / math.comb(total_unseen, opp_total_cards)
            p_beat = 1.0 - p_none
        if pass_caps and move.order_value >= pass_caps.get("max_single_cap", 99):
            p_beat *= (0.05 if all_no_two else 0.20)
        return p_beat

    # 2. ĐÔI (PAIR)
    if move.combo_type == SamComboType.PAIR:
        if move.order_value == RANK_2 or draw_k < 2:
            return 0.0
        all_no_two = bool(pass_caps and pass_caps.get("all_opps_no_two"))
        p_no_higher_pair_single_opp = 1.0
        for r, cnt in unseen_ranks.items():
            if r > move.order_value and cnt >= 2 and not (all_no_two and r == RANK_2):
                p_0 = (
                    math.comb(total_unseen - cnt, draw_k) / total_ways
                    if total_unseen - cnt >= draw_k
                    else 0.0
                )
                p_1 = (
                    (cnt * math.comb(total_unseen - cnt, draw_k - 1)) / total_ways
                    if total_unseen - cnt >= draw_k - 1
                    else 0.0
                )
                p_ge_2 = max(0.0, 1.0 - p_0 - p_1)
                p_no_higher_pair_single_opp *= (1.0 - p_ge_2)
        p_one_opp_has = 1.0 - p_no_higher_pair_single_opp
        p_beat = 1.0 - ((1.0 - p_one_opp_has) ** num_opponents)
        if pass_caps and move.order_value >= pass_caps.get("max_pair_cap", 99):
            p_beat *= 0.18
        return p_beat

    # 3. SÁM CÔ (TRIPLE)
    if move.combo_type == SamComboType.TRIPLE:
        if move.order_value == RANK_2 or draw_k < 3:
            return 0.0
        p_no_higher_triple_single_opp = 1.0
        for r, cnt in unseen_ranks.items():
            if r > move.order_value and cnt >= 3:
                if cnt == 3:
                    p_ge_3 = (
                        math.comb(total_unseen - 3, draw_k - 3) / total_ways
                        if total_unseen - 3 >= draw_k - 3
                        else 0.0
                    )
                else:  # cnt == 4
                    p_3 = (
                        (4 * math.comb(total_unseen - 4, draw_k - 3)) / total_ways
                        if total_unseen - 4 >= draw_k - 3
                        else 0.0
                    )
                    p_4 = (
                        math.comb(total_unseen - 4, draw_k - 4) / total_ways
                        if draw_k >= 4 and total_unseen - 4 >= draw_k - 4
                        else 0.0
                    )
                    p_ge_3 = p_3 + p_4
                p_no_higher_triple_single_opp *= (1.0 - p_ge_3)
        p_one_opp_has = 1.0 - p_no_higher_triple_single_opp
        p_beat = 1.0 - ((1.0 - p_one_opp_has) ** num_opponents)
        if pass_caps and move.order_value >= pass_caps.get("max_triple_cap", 99):
            p_beat *= 0.15
        return p_beat

    # 4. TỨ QUÝ (FOUR_OF_KIND)
    if move.combo_type == SamComboType.FOUR_OF_KIND:
        if draw_k < 4 or total_unseen < 4:
            return 0.0
        higher_quads = [r for r, cnt in unseen_ranks.items() if r > move.order_value and cnt == 4]
        if not higher_quads:
            return 0.0
        p_quad = math.comb(total_unseen - 4, draw_k - 4) / total_ways
        return min(1.0, len(higher_quads) * num_opponents * p_quad)

    # 5. SẢNH (STRAIGHT)
    if move.combo_type == SamComboType.STRAIGHT:
        L = move.length
        if draw_k < L:
            return 0.0
        max_ord = straight_max_order_value(L)
        if move.order_value >= max_ord:
            return 0.0  # Sảnh thượng tới A (vd Q-K-A, 10-J-Q-K-A): Bất bại!

        avail_factor = 0.72 if L >= 4 else 0.85
        p_no_higher_straight_one_opp = 1.0
        prev_p_have_all = 0.0
        prev_first_p_r = 0.0
        for cand_ord in range(move.order_value + 1, max_ord + 1):
            if cand_ord == 1:
                req = [RANK_2] + list(range(RANK_3, RANK_3 + L - 1))
            else:
                start_r = cand_ord - 2
                req = list(range(start_r, start_r + L))
            if any(unseen_ranks[r] == 0 for r in req):
                prev_p_have_all = 0.0
                prev_first_p_r = 0.0
                continue
            p_have_all = 1.0
            first_p_r = 0.0
            for idx_r, r in enumerate(req):
                cnt = unseen_ranks[r]
                rem_draws = max(1, draw_k - idx_r)
                rem_deck = max(rem_draws, total_unseen - idx_r)
                denom = math.comb(rem_deck, rem_draws)
                if denom == 0 or rem_deck - cnt < rem_draws:
                    p_r = 1.0
                else:
                    p_r = 1.0 - (math.comb(rem_deck - cnt, rem_draws) / denom)
                if idx_r == 0:
                    first_p_r = p_r
                p_have_all *= p_r
            eff_win = p_have_all * avail_factor
            if cand_ord > move.order_value + 1 and prev_p_have_all > 0.0:
                eff_win *= max(0.15, 1.0 - prev_first_p_r * 0.78)
            p_no_higher_straight_one_opp *= (1.0 - min(0.98, eff_win))
            prev_p_have_all = p_have_all
            prev_first_p_r = first_p_r

        p_one_opp = 1.0 - p_no_higher_straight_one_opp
        p_beat = 1.0 - ((1.0 - p_one_opp) ** num_opponents)
        if pass_caps and move.order_value >= pass_caps.get("max_straight_cap", {}).get(L, 99):
            p_beat *= 0.18
        return p_beat

    return 0.5


def _generate_candidate_xin_sam_sequences(
    hand: Sequence[int],
    unseen_ranks: Counter,
    num_opponents: int,
) -> List[List[SamCombo]]:
    """
    Sinh tập các chuỗi đánh hoàn chỉnh `pi = (m_1, m_2, ..., m_k)` phân hoạch hết 10 lá bài `hand`
    sao cho nước cuối `m_k` hợp lệ (không phải bộ 2) và các nước dẫn `m_1 .. m_{k-1}` được
    sắp xếp từ an toàn nhất (xác suất bị chặn nhỏ nhất) đến rủi ro cao hơn, đẩy bộ yếu nhất
    xuống làm nước kết thúc `m_k`.
    """
    sorted_hand = tuple(sorted(hand))
    all_combos = generate_all_sam_combos(sorted_hand)

    # Nếu có Sảnh Rồng / Sảnh 10 lá ăn trắng hoặc đi 1 nước hết bài ngay:
    ten_card_combos = [c for c in all_combos if c.length == len(sorted_hand) and not c.is_all_twos]
    if ten_card_combos:
        best_ten = max(ten_card_combos, key=lambda c: c.order_value)
        return [[best_ten]]

    multi_by_cards: Dict[Tuple[int, ...], SamCombo] = {}
    for c in all_combos:
        if c.length >= 2:
            multi_by_cards[c.cards] = c
    multi_combos = list(multi_by_cards.values())
    multi_combos.sort(key=lambda c: (-c.length, -int(c.combo_type), -c.order_value))

    raw_partitions: List[List[SamCombo]] = []

    def dfs(idx: int, used_mask: int, chosen: List[SamCombo]) -> None:
        leftover = [sorted_hand[k] for k in range(len(sorted_hand)) if not (used_mask & (1 << k))]
        full_part = list(chosen) + [
            SamCombo(SamComboType.SINGLE, (c,), 1, card_rank(c), f"Lẻ {RANK_NAMES[card_rank(c)]}")
            for c in leftover
        ]
        # Chỉ xét các cách chia bài có số lượt <= 5 (vì >= 6 lượt gần như không bao giờ Xin Sâm thành công)
        if len(full_part) <= 5:
            raw_partitions.append(full_part)

        if len(leftover) < 2 or len(chosen) >= 4:
            return

        for m_idx in range(idx, len(multi_combos)):
            mc = multi_combos[m_idx]
            if mc.length > len(leftover):
                continue
            m_mask = 0
            ok = True
            for card in mc.cards:
                pos = sorted_hand.index(card)
                if used_mask & (1 << pos):
                    ok = False
                    break
                m_mask |= (1 << pos)
            if ok:
                chosen.append(mc)
                dfs(m_idx + 1, used_mask | m_mask, chosen)
                chosen.pop()

    dfs(0, 0, [])

    # Nếu bài quá xấu không có cách chia nào <= 5 lượt, lấy cách chia tối ưu từ DP
    if not raw_partitions:
        dp_plan = optimal_partition_sam_hand(sorted_hand)
        raw_partitions.append(dp_plan.combos)

    # Với mỗi phân hoạch, tìm cách sắp thứ tự đánh (m_1, ..., m_k) tốt nhất:
    # - Nước cuối m_k: Chọn bộ KHÔNG PHẢI QUÂN 2 có xác suất bị chặn CAO NHẤT (tức bộ yếu nhất trên tay)
    #   để giấu nó ở lượt hạ bài cuối cùng!
    # - Các nước dẫn m_1 .. m_{k-1}: Sắp xếp theo xác suất bị chặn tăng dần (đánh các bộ Bất bại /
    #   Sảnh lớn / Heo / Đôi lớn trước).
    candidate_sequences: List[Tuple[float, List[SamCombo]]] = []
    for part in raw_partitions:
        non_two_indices = [i for i, cb in enumerate(part) if not cb.is_all_twos]
        if not non_two_indices:
            continue  # Phân hoạch toàn 2 -> Không thể về nhất hợp lệ

        # Tính xác suất bị chặn giải tích cho từng bộ trong phân hoạch
        probs = [_analytic_single_move_beaten_prob(cb, unseen_ranks, num_opponents) for cb in part]

        def _is_xin_sam_boss_lead(cb: SamCombo, p_beat: float) -> bool:
            if p_beat <= 1e-9 or cb.is_all_twos or cb.combo_type == SamComboType.FOUR_OF_KIND:
                return True
            if cb.combo_type == SamComboType.TRIPLE and cb.order_value >= RANK_A:
                return True
            return False

        # Chọn ứng viên làm nước kết thúc m_k: ưu tiên giấu bộ KHÔNG phải Boss/Sám A/Tứ quý (VD Sảnh 4-10 ở ván 19:10:48)
        # xuống lượt hạ bài cuối cùng, để đánh Sám A / Tứ quý / Bộ bất bại ra trước!
        best_last_idx = max(
            non_two_indices,
            key=lambda i: (
                0 if _is_xin_sam_boss_lead(part[i], probs[i]) else 1,
                probs[i],
                -part[i].order_value,
                part[i].length,
            ),
        )
        last_combo = part[best_last_idx]
        lead_combos = [part[i] for i in range(len(part)) if i != best_last_idx]
        # Sắp xếp các nước dẫn theo độ an toàn giảm dần:
        # Ưu tiên đánh các bộ bất bại / Sám A / Tứ quý hoặc bộ nhiều lá có rủi ro cực thấp (<= 10%) trước
        lead_combos.sort(
            key=lambda cb: (
                0 if _is_xin_sam_boss_lead(cb, _analytic_single_move_beaten_prob(cb, unseen_ranks, num_opponents)) else 1,
                0 if (cb.length >= 2 and not cb.is_all_twos and _analytic_single_move_beaten_prob(cb, unseen_ranks, num_opponents) <= 0.10) else 1,
                _analytic_single_move_beaten_prob(cb, unseen_ranks, num_opponents),
                -cb.length,
                -cb.order_value,
            )
        )
        seq = lead_combos + [last_combo]
        # Ước lượng xác suất sống sót qua chuỗi dẫn m_1 .. m_{k-1}
        p_survive_analytic = 1.0
        for cb in lead_combos:
            p_survive_analytic *= (1.0 - _analytic_single_move_beaten_prob(cb, unseen_ranks, num_opponents))
        candidate_sequences.append((p_survive_analytic, seq))

    candidate_sequences.sort(key=lambda item: -item[0])
    # Trả về tối đa 6 chuỗi ứng viên mạnh nhất để chạy kiểm định Monte Carlo + Giải tích chính xác
    unique_seqs: List[List[SamCombo]] = []
    seen_keys = set()
    for _, seq in candidate_sequences:
        key = tuple(cb.cards for cb in seq)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_seqs.append(seq)
            if len(unique_seqs) >= 6:
                break
    return unique_seqs


def _opponent_can_beat_move_fast(
    move: SamCombo,
    opp_ranks: Counter,
) -> bool:
    """
    Kiểm tra siêu tốc (O(1)) xem một đối thủ với phân bố số bài `opp_ranks` (10 lá)
    có bất kỳ bộ hợp lệ nào chặn được `move` hay không.
    Do Sâm Lốc KHÔNG PHÂN BIỆT CHẤT nên chỉ cần kiểm tra tần suất rank `opp_ranks`!
    """
    if move.combo_type == SamComboType.SINGLE:
        if move.order_value == RANK_2:
            # Chỉ Tứ quý mới chặt được 2 lẻ
            return any(cnt == 4 for cnt in opp_ranks.values())
        return any(r > move.order_value and cnt >= 1 for r, cnt in opp_ranks.items())

    if move.combo_type == SamComboType.PAIR:
        if move.order_value == RANK_2:
            return False
        return any(r > move.order_value and cnt >= 2 for r, cnt in opp_ranks.items())

    if move.combo_type == SamComboType.TRIPLE:
        if move.order_value == RANK_2:
            return False
        return any(r > move.order_value and cnt >= 3 for r, cnt in opp_ranks.items())

    if move.combo_type == SamComboType.FOUR_OF_KIND:
        return any(r > move.order_value and cnt == 4 for r, cnt in opp_ranks.items())

    if move.combo_type == SamComboType.STRAIGHT:
        L = move.length
        max_ord = straight_max_order_value(L)
        if move.order_value >= max_ord:
            return False
        for cand_ord in range(move.order_value + 1, max_ord + 1):
            if cand_ord == 1:
                # Sảnh 2-3-4-...
                if opp_ranks[RANK_2] >= 1 and all(opp_ranks[r] >= 1 for r in range(RANK_3, RANK_3 + L - 1)):
                    return True
            else:
                start_r = cand_ord - 2
                if all(opp_ranks[r] >= 1 for r in range(start_r, start_r + L)):
                    return True
        return False

    return False


def evaluate_xin_sam(
    hand: Sequence[int],
    num_players: int = 4,
    max_risk_percent: float = 10.0,
    num_simulations: int = 300,
    rng: Optional[random.Random] = None,
) -> XinSamAnalysis:
    """
    HÀM TRỌNG TÂM: Tính toán xác suất thành công, độ mạo hiểm (% Risk) và Kỳ vọng (EV)
    để quyết định có XIN SÂM (Báo Sâm) hay không dựa trên ngưỡng mạo hiểm đầu vào `max_risk_percent`.

    Tham số:
    - `hand`: 10 lá bài trên tay (list các số 0..51).
    - `num_players`: Tổng số người chơi trên bàn (2 đến 5 người).
    - `max_risk_percent`: Ngưỡng % mạo hiểm tối đa cho phép (0.0 -> 100.0).
      Ví dụ:
        + `max_risk_percent = 0.0`: Chỉ Xin Sâm khi bài BẤT BẠI tuyệt đối 100% (Rủi ro = 0%).
        + `max_risk_percent = 10.0`: Xin Sâm khi xác suất bị bắt <= 10% (Tỷ lệ ăn Sâm >= 90%).
        + `max_risk_percent = 25.0`: Xin Sâm khi xác suất bị bắt <= 25% (Tỷ lệ ăn Sâm >= 75%).
        + `max_risk_percent = 50.0`: Điểm hòa vốn lý thuyết (EV >= 0, tỷ lệ ăn Sâm >= 50%).
    - `num_simulations`: Số lượng ván chia bài ngẫu nhiên Monte Carlo cho (N-1) đối thủ để
      đo chính xác tương quan đồng thời giữa các nước đi.
    """
    num_opponents = max(1, min(4, num_players - 1))
    hand_set = set(hand)
    unseen_cards = [c for c in range(52) if c not in hand_set]
    unseen_ranks = Counter(card_rank(c) for c in unseen_cards)

    candidates = _generate_candidate_xin_sam_sequences(hand, unseen_ranks, num_opponents)
    if not candidates:
        return XinSamAnalysis(
            should_declare=False,
            win_probability=0.0,
            risk_percent=100.0,
            max_risk_percent=max_risk_percent,
            expected_value_cards=-float(ACTIVE_SAM_RULE.bao_sam) * num_opponents,
            planned_sequence=[],
            step_risks=[],
            reason="Không có chuỗi thoát bài hợp lệ (bị kẹt toàn quân 2 ở cuối bài).",
        )

    sim_rng = rng if rng is not None else random.Random(42 + sum(hand) * 17 + num_players)

    # Tạo trước `num_simulations` mẫu chia bài cho `num_opponents` đối thủ (mỗi người 10 lá)
    sampled_opp_rank_counters: List[List[Counter]] = []
    unseen_rank_list = [card_rank(c) for c in unseen_cards]
    for _ in range(num_simulations):
        shuffled_ranks = list(unseen_rank_list)
        sim_rng.shuffle(shuffled_ranks)
        opp_hands = [
            Counter(shuffled_ranks[i * 10 : (i + 1) * 10])
            for i in range(num_opponents)
        ]
        sampled_opp_rank_counters.append(opp_hands)

    best_seq: List[SamCombo] = candidates[0]
    best_win_prob: float = -1.0
    best_step_risks: List[Tuple[SamCombo, float]] = []

    for seq in candidates:
        lead_moves = seq[:-1]
        last_move = seq[-1]

        # 1. Tính xác suất giải tích (Exact/Analytic Hypergeometric) không bị chặn ở từng bước dẫn
        analytic_survive = 1.0
        step_risks: List[Tuple[SamCombo, float]] = []
        for mv in lead_moves:
            p_beaten = _analytic_single_move_beaten_prob(mv, unseen_ranks, num_opponents)
            analytic_survive *= (1.0 - p_beaten)
            step_risks.append((mv, p_beaten * 100.0))
        # Bước cuối (hạ nốt bộ cuối cùng để hết bài -> rủi ro bị chặn = 0% nếu các bước dẫn đã giữ cái!)
        step_risks.append((last_move, 0.0))

        # 2. Kiểm định Monte Carlo trên `num_simulations` ván bài đối thủ thực tế
        mc_wins = 0
        for opp_hands in sampled_opp_rank_counters:
            caught = False
            for mv in lead_moves:
                if any(_opponent_can_beat_move_fast(mv, opp_rc) for opp_rc in opp_hands):
                    caught = True
                    break
            if not caught:
                mc_wins += 1
        mc_win_prob = mc_wins / max(1, num_simulations)

        # Kết hợp xác suất Monte Carlo (80% trọng số vì bắt chính xác tương quan nhiều lượt)
        # và xác suất Giải tích Hypergeometric (20% trọng số để làm mượt các sự kiện hiếm như Tứ quý):
        combined_win_prob = 0.80 * mc_win_prob + 0.20 * analytic_survive

        if combined_win_prob > best_win_prob:
            best_win_prob = combined_win_prob
            best_seq = seq
            best_step_risks = step_risks

    best_win_prob = max(0.0, min(1.0, best_win_prob))
    risk_pct = (1.0 - best_win_prob) * 100.0
    ev_cards = float(ACTIVE_SAM_RULE.bao_sam) * num_opponents * (2.0 * best_win_prob - 1.0)
    risky_lead_steps = sum(1 for _, r_pct in best_step_risks[:-1] if r_pct > 1.0)
    eff_max_risk = min(max_risk_percent, 4.0) if risky_lead_steps >= 2 else max_risk_percent
    should_declare = (risk_pct <= eff_max_risk + 1e-6)

    seq_str = " -> ".join(repr(cb) for cb in best_seq)
    if should_declare:
        reason = (
            f"ĐỦ ĐIỀU KIỆN XIN SÂM: Rủi ro = {risk_pct:.2f}% <= Ngưỡng cho phép {max_risk_percent:.1f}% "
            f"(Xác suất ăn Sâm = {best_win_prob * 100:.2f}%, EV = {ev_cards:+.1f} lá). "
            f"Lộ trình đánh: {seq_str}"
        )
    else:
        reason = (
            f"KHÔNG XIN SÂM: Rủi ro = {risk_pct:.2f}% > Ngưỡng cho phép {max_risk_percent:.1f}% "
            f"(Xác suất ăn Sâm = {best_win_prob * 100:.2f}%, EV = {ev_cards:+.1f} lá). "
            f"Lộ trình tốt nhất nếu liều: {seq_str}"
        )

    return XinSamAnalysis(
        should_declare=should_declare,
        win_probability=best_win_prob,
        risk_percent=risk_pct,
        max_risk_percent=max_risk_percent,
        expected_value_cards=ev_cards,
        planned_sequence=best_seq,
        step_risks=best_step_risks,
        reason=reason,
    )


# ============================================================================
# 5. TRẠNG THÁI BÀN CHƠI & CÁC ĐỐI THỦ AI (PRO BOTS & SMART MATH BOT)
# ============================================================================

@dataclass
class SamTableState:
    num_players: int
    my_seat: int
    my_hand: List[int]
    board_combo: Optional[SamCombo]
    board_owner: Optional[int]
    cards_left: List[int]              # Số lá còn lại của từng nhà (khởi đầu = 10)
    played_cards: List[int]            # Tất cả các lá bài đã đánh ra trên bàn
    passed_in_round: List[bool]        # Những ai đã bỏ lượt trong vòng hiện tại
    xin_sam_player: Optional[int] = None  # Seat của người đang Báo Sâm (nếu có)
    history: List[Tuple[int, SamCombo]] = field(default_factory=list)
    # [V4.9.8] mỗi lượt đối thủ BỎ: (bộ trên bàn lúc đó, các lá đối thủ đó đánh ra SAU lượt bỏ) - theo ghế
    opp_pass_log: Dict[int, List[Tuple[SamCombo, Tuple[int, ...]]]] = field(default_factory=dict)

    @property
    def next_active_seat(self) -> int:
        for offset in range(1, self.num_players):
            s = (self.my_seat + offset) % self.num_players
            if self.cards_left[s] > 0:
                return s
        return (self.my_seat + 1) % self.num_players

    @property
    def next_player_card_count(self) -> int:
        return self.cards_left[self.next_active_seat]

    @property
    def min_opponent_cards(self) -> int:
        opp_counts = [
            self.cards_left[s]
            for s in range(self.num_players)
            if s != self.my_seat and self.cards_left[s] > 0
        ]
        return min(opp_counts) if opp_counts else 10

    @property
    def max_opponent_cards(self) -> int:
        opp_counts = [
            self.cards_left[s]
            for s in range(self.num_players)
            if s != self.my_seat and self.cards_left[s] > 0
        ]
        return max(opp_counts) if opp_counts else 10


class BaseSamBot:
    def __init__(self, name: str, xin_sam_max_risk_pct: float = 10.0):
        self.name = name
        self.xin_sam_max_risk_pct = xin_sam_max_risk_pct
        self._xin_sam_plan: List[SamCombo] = []

    def reset_for_new_hand(self) -> None:
        self._xin_sam_plan = []

    def decide_xin_sam(self, hand: Sequence[int], num_players: int) -> XinSamAnalysis:
        analysis = evaluate_xin_sam(
            hand=hand,
            num_players=num_players,
            max_risk_percent=self.xin_sam_max_risk_pct,
        )
        if analysis.should_declare:
            self._xin_sam_plan = list(analysis.planned_sequence)
        else:
            self._xin_sam_plan = []
        return analysis

    def choose_move(self, state: SamTableState) -> SamCombo:
        raise NotImplementedError


class SamGreedyBot(BaseSamBot):
    """Bot Tham lam cơ bản: Luôn đánh bộ nhỏ nhất hợp lệ, tôn trọng luật Giữ Cửa & Cấm về bằng 2."""

    def choose_move(self, state: SamTableState) -> SamCombo:
        legal = get_legal_sam_moves(
            state.my_hand,
            state.board_combo,
            state.next_player_card_count,
        )
        non_pass = [m for m in legal if not m.is_pass]
        if not non_pass:
            return PASS_COMBO
        safe = [m for m in non_pass if not would_leave_only_twos(state.my_hand, m)]
        pool = safe if safe else non_pass
        if state.board_combo is None or state.board_combo.is_pass:
            pool.sort(key=lambda m: (-m.length, m.order_value))
            return pool[0]
        pool.sort(key=lambda m: (m.order_value, -m.length))
        return pool[0]


class SamRuleBot(BaseSamBot):
    """Bot Luật truyền thống: Giữ 2 và Tứ quý lại, ưu tiên đánh sảnh/bộ trước, lẻ sau."""

    def choose_move(self, state: SamTableState) -> SamCombo:
        legal = get_legal_sam_moves(
            state.my_hand,
            state.board_combo,
            state.next_player_card_count,
        )
        non_pass = [m for m in legal if not m.is_pass]
        if not non_pass:
            return PASS_COMBO

        # Nếu đi 1 nước hết bài hợp lệ -> đánh ngay
        for m in non_pass:
            if m.length == len(state.my_hand) and not m.is_all_twos:
                return m

        safe = [m for m in non_pass if not would_leave_only_twos(state.my_hand, m)]
        pool = safe if safe else non_pass

        if state.board_combo is None or state.board_combo.is_pass:
            # Mở vòng: ưu tiên đánh bộ dài (Sảnh/Sám/Đôi) không chứa 2
            no_two = [m for m in pool if not m.contains_two]
            use_pool = no_two if no_two else pool
            use_pool.sort(key=lambda m: (-m.length, m.order_value))
            return use_pool[0]

        # Đỡ bài: nếu đối thủ còn >= 4 lá thì không vội tung 2 hay Tứ quý
        if state.min_opponent_cards >= 4:
            normal_resp = [
                m for m in pool
                if m.combo_type != SamComboType.FOUR_OF_KIND and not m.is_all_twos
            ]
            if normal_resp:
                normal_resp.sort(key=lambda m: (m.order_value, -m.length))
                return normal_resp[0]
            return PASS_COMBO if PASS_COMBO in legal else pool[0]

        pool.sort(key=lambda m: (m.order_value, -m.length))
        return pool[0]


class SamProShedderBot(BaseSamBot):
    """Pro Bot 1 - Tối ưu hóa thoát bài nhanh bằng Quy hoạch động (DP Shedder)."""

    def choose_move(self, state: SamTableState) -> SamCombo:
        legal = get_legal_sam_moves(
            state.my_hand,
            state.board_combo,
            state.next_player_card_count,
        )
        non_pass = [m for m in legal if not m.is_pass]
        if not non_pass:
            return PASS_COMBO

        for m in non_pass:
            if m.length == len(state.my_hand) and not m.is_all_twos:
                return m

        best_move = non_pass[0]
        best_val = -1e9
        for m in legal:
            if m.is_pass:
                cur_plan = optimal_partition_sam_hand(state.my_hand)
                val = cur_plan.total_score - 3.5
            else:
                rem = [c for c in state.my_hand if c not in m.cards]
                rem_plan = optimal_partition_sam_hand(rem)
                val = rem_plan.total_score + m.length * 2.2 - m.order_value * 0.25
                if would_leave_only_twos(state.my_hand, m):
                    val -= 50.0
            if val > best_val:
                best_val = val
                best_move = m
        return best_move


class SamProCounterBot(BaseSamBot):
    """Pro Bot 2 - Chuyên gia đếm bài & rình bắt 2 / chặn cửa (Card Counter Pro)."""

    def choose_move(self, state: SamTableState) -> SamCombo:
        legal = get_legal_sam_moves(
            state.my_hand,
            state.board_combo,
            state.next_player_card_count,
        )
        non_pass = [m for m in legal if not m.is_pass]
        if not non_pass:
            return PASS_COMBO

        for m in non_pass:
            if m.length == len(state.my_hand) and not m.is_all_twos:
                return m

        known = set(state.my_hand) | set(state.played_cards)
        unseen = [c for c in range(52) if c not in known]

        best_move = non_pass[0]
        best_val = -1e9
        for m in legal:
            if m.is_pass:
                plan = optimal_partition_sam_hand(state.my_hand, unseen)
                val = plan.total_score - (6.0 if state.min_opponent_cards <= 2 else 2.2)
            else:
                rem = [c for c in state.my_hand if c not in m.cards]
                plan = optimal_partition_sam_hand(rem, unseen)
                val = plan.total_score + m.length * 2.5
                if is_boss_sam_combo(m, unseen) and len(rem) >= 3 and state.min_opponent_cards >= 4:
                    # Giữ lại bài Boss nếu chưa cần thiết
                    val -= 6.5
                if state.min_opponent_cards <= 2:
                    val += m.order_value * 0.8 + m.length * 3.0
                if would_leave_only_twos(state.my_hand, m):
                    val -= 60.0
            if val > best_val:
                best_val = val
                best_move = m
        return best_move


def _sam_tester_adjust(state: "SamTableState", base: SamCombo) -> SamCombo:
    """Áp luật tester lên nước gốc (xem SamSmartMathBot.tester_rule)."""
    hand = list(state.my_hand)
    legal = get_legal_sam_moves(hand, state.board_combo, state.next_player_card_count)
    keys = {tuple(sorted(m.cards)): m for m in legal}
    if state.board_combo is None:
        if tuple(sorted(hand)) in keys and classify_sam_cards(hand) is not None:
            return base
        plan = optimal_partition_sam_hand(hand)
        if len(plan.combos) <= 2:
            return base
        singles = [m for m in plan.combos if len(m.cards) == 1 and not all(card_rank(c) == RANK_2 for c in m.cards)]
        pairs = [m for m in plan.combos if m.combo_type == SamComboType.PAIR and not all(card_rank(c) == RANK_2 for c in m.cards)]
        if singles and len(singles) >= max(len(pairs), 1):
            pick = min(singles, key=lambda m: m.order_value)
        elif pairs and len(pairs) > len(singles):
            pick = min(pairs, key=lambda m: m.order_value)
        else:
            return base
        return keys.get(tuple(sorted(pick.cards)), base)
    b = state.board_combo
    if (not base.is_pass and base.is_all_twos and len(base.cards) == 2 and b.combo_type == SamComboType.PAIR
            and not b.is_all_twos):
        if len(hand) != 2 and state.min_opponent_cards > 2 and len(hand) > 4:
            return PASS_COMBO
    return base


# [V4.7] "HỌC NGƯỜI THẮNG" SÂM: điểm cộng theo thói quen NGƯỜI THẮNG ván trong log thật HIT
# (clone_v7/mo_hinh_nguoi_sam.py: logit có điều kiện 1.586 lượt người thắng 27-28/10; đoán đúng 56.5% trên ván 29-30/10, bừa 23%).
HUMAN_PRIOR_SAM_W = {"đi|đầu|lẻ": 0.085, "đi|đầu|đôi": 0.4477, "đi|đầu|sám": 0.9416, "đi|đầu|sảnh": -0.5644, "đi|đầu|heo": -0.8551, "đi|đầu|hàng": -0.0548, "đi|giữa|lẻ": -0.5892, "đi|giữa|đôi": 0.6139, "đi|giữa|sám": 0.602, "đi|giữa|sảnh": -0.2143, "đi|giữa|heo": -0.5082, "đi|giữa|hàng": 0.0958, "đi|cuối|lẻ": -1.9349, "đi|cuối|đôi": 0.6327, "đi|cuối|sám": 0.3604, "đi|cuối|sảnh": 0.5244, "đi|cuối|heo": 0.4174, "chặn|đầu|bỏ lượt": -1.0106, "chặn|đầu|lẻ": 0.1008, "chặn|đầu|đôi": 0.1907, "chặn|đầu|sám": -0.0943, "chặn|đầu|sảnh": 0.0716, "chặn|đầu|heo": 0.7352, "chặn|đầu|hàng": 0.0065, "chặn|giữa|bỏ lượt": -1.26, "chặn|giữa|lẻ": 0.0324, "chặn|giữa|đôi": 0.2179, "chặn|giữa|sám": 0.0065, "chặn|giữa|sảnh": 0.1292, "chặn|giữa|heo": 0.8673, "chặn|giữa|hàng": 0.0065, "chặn|cuối|bỏ lượt": -1.0339, "chặn|cuối|lẻ": 0.1356, "chặn|cuối|đôi": 0.1624, "chặn|cuối|sảnh": 0.0287, "chặn|cuối|heo": 0.7073, "đi|phá bộ": -3.3561, "chặn|phá bộ": -2.3286, "đi|lẻ nhỏ nhất": 1.0598, "chặn|nhỏ nhất cùng loại": 0.9112, "chặn|bỏ lượt khi chặn được bằng bài thường": -2.0108, "đi|bộ cuối về luôn": 0.4183, "đi|bộ không ai chặn được": -0.8298, "đi|sảnh dài nhất": 1.0186}


def _sam_human_kind(m: SamCombo) -> str:
    if m.is_pass:
        return "bỏ lượt"
    if m.is_all_twos:
        return "heo"
    return {SamComboType.SINGLE: "lẻ", SamComboType.PAIR: "đôi", SamComboType.TRIPLE: "sám",
            SamComboType.STRAIGHT: "sảnh"}.get(m.combo_type, "hàng")


def sam_human_prior_scores(state: "SamTableState", legal: List[SamCombo]) -> Dict[SamCombo, float]:
    """Điểm "người thắng hay chọn" (logit) cho từng nước hợp lệ."""
    hand = list(state.my_hand)
    board = state.board_combo
    lead = board is None or board.is_pass
    side = "đi" if lead else "chặn"
    n = len(hand)
    p = "đầu" if n >= 8 else ("giữa" if n >= 5 else "cuối")
    plan = optimal_partition_sam_hand(hand)
    big = [set(c.cards) for c in plan.combos]
    plain = any(not m.is_pass and not m.is_all_twos for m in legal)
    min_by: Dict[Tuple[int, int], int] = {}
    for m in legal:
        if not m.is_pass:
            k = (int(m.combo_type), len(m.cards))
            min_by[k] = min(min_by.get(k, 99), m.order_value)
    low = min(card_rank(c) for c in hand) if hand else 0
    longest = max((len(m.cards) for m in legal if m.combo_type == SamComboType.STRAIGHT), default=0)
    unseen = [c for c in range(52) if c not in set(hand) and c not in set(state.played_cards)]
    W = HUMAN_PRIOR_SAM_W
    out: Dict[SamCombo, float] = {}
    for m in legal:
        v = W.get(f"{side}|{p}|{_sam_human_kind(m)}", 0.0)
        if m.is_pass:
            if plain and not lead:
                v += W.get("chặn|bỏ lượt khi chặn được bằng bài thường", 0.0)
            out[m] = v
            continue
        cs = set(m.cards)
        if any((cs & b) and len(b) > len(cs) for b in big):
            v += W.get(f"{side}|phá bộ", 0.0)
        if lead and m.combo_type == SamComboType.SINGLE and card_rank(m.cards[0]) == low:
            v += W.get("đi|lẻ nhỏ nhất", 0.0)
        if not lead and min_by.get((int(m.combo_type), len(m.cards))) == m.order_value:
            v += W.get("chặn|nhỏ nhất cùng loại", 0.0)
        if lead and len(m.cards) == len(hand):
            v += W.get("đi|bộ cuối về luôn", 0.0)
        if lead and len(m.cards) >= 2 and is_boss_sam_combo(m, unseen):
            v += W.get("đi|bộ không ai chặn được", 0.0)
        if lead and m.combo_type == SamComboType.STRAIGHT and len(m.cards) == longest:
            v += W.get("đi|sảnh dài nhất", 0.0)
        if lead and m.combo_type == SamComboType.STRAIGHT and len(m.cards) >= 4:
            v += 1.35 + 0.25 * (len(m.cards) - 4)
        out[m] = v
    return out


def _sam_unseen(state: "SamTableState") -> List[int]:
    known = set(state.my_hand) | set(state.played_cards)
    return [c for c in range(52) if c not in known]


def _sam_keep_boss_adjust(state: "SamTableState", base: SamCombo) -> SamCombo:
    """[V4.9.30/V5.0] Giữ BỘ ĐỠ cùng loại: chỉ khi đang cầm lượt, định đánh bộ BẤT BẠI (Q-K-A, đôi/sám lớn nhất...) mà trên tay
    có sẵn 1 bộ YẾU HƠN CÙNG LOẠI & CÙNG ĐỘ DÀI trong phân hoạch tối ưu -> đánh bộ yếu hơn trước để bộ bất bại che."""
    if state.board_combo is not None or base.is_pass or base.combo_type == SamComboType.SINGLE or base.is_all_twos:
        return base
    hand = list(state.my_hand)
    if len(base.cards) >= len(hand) or state.min_opponent_cards <= 2:
        return base
    unseen = _sam_unseen(state)
    pass_caps = _extract_sam_opp_pass_caps(state)
    if not _is_effective_boss_sam_combo(base, unseen, pass_caps):
        return base
    plan = optimal_partition_sam_hand(hand, unseen)
    same_kind_weaker = sorted(
        (
            m for m in plan.combos
            if m.combo_type == base.combo_type
            and len(m.cards) == len(base.cards)
            and m.order_value < base.order_value
            and not _is_effective_boss_sam_combo(m, unseen, pass_caps)
        ),
        key=lambda m: m.order_value,
    )
    if not same_kind_weaker:
        return base
    legal = get_legal_sam_moves(hand, None, state.next_player_card_count)
    for m in legal:
        if tuple(sorted(m.cards)) == tuple(sorted(same_kind_weaker[0].cards)) and not would_leave_only_twos(hand, m):
            return m
    return base


def _sam_keep_straight_adjust(state: "SamTableState", base: SamCombo, mode: str) -> SamCombo:
    """Giữ SẢNH làm bộ đỡ: được đi mà nước gốc là sảnh, còn lá rác lẻ -> đánh lá rác nhỏ nhất trước."""
    kb = _sam_keep_boss_adjust(state, base)
    if kb is not base:
        return kb
    if state.board_combo is not None or base.is_pass or base.combo_type != SamComboType.STRAIGHT:
        return base
    hand = list(state.my_hand)
    if len(base.cards) == len(hand):
        return base
    n = len(hand)
    if mode == "giu_sanh" and n >= 8:
        return base
    plan = optimal_partition_sam_hand(hand)
    junk = sorted((m for m in plan.combos if len(m.cards) == 1 and card_rank(m.cards[0]) not in (RANK_2,)),
                  key=lambda m: m.order_value)
    need = 2 if n < 8 else 3
    if len(junk) < need or state.min_opponent_cards <= 2:
        return base
    legal = get_legal_sam_moves(hand, None, state.next_player_card_count)
    for m in legal:
        if tuple(sorted(m.cards)) == tuple(sorted(junk[0].cards)):
            return m
    return base


class SamSmartMathBot(BaseSamBot):
    """
    ==================================================================================
    SIÊU AI TOÁN HỌC SÂM LỐC: SamSmartMathBot
    ==================================================================================
    Tích hợp 6 trụ cột toán học chuyên biệt cho Sâm Lốc SUN:
    1. Quy hoạch động Phân rã Bài Sâm Lốc (`optimal_partition_sam_hand`) với sảnh A-2-3 / 2-3-4.
    2. Hệ thống Xin Sâm (Báo Sâm) theo % mạo hiểm (`evaluate_xin_sam` với `xin_sam_max_risk_pct`):
       - Khi đã Xin Sâm, thực thi chính xác lộ trình bất bại `planned_sequence`.
       - Khi đối thủ Xin Sâm, kích hoạt chế độ "Săn Sâm" (tung bộ lớn nhất chặn đứng ngay lập tức).
    3. Xác suất Hypergeometric & Đếm bài (Card Counting) không phân biệt chất:
       - Tính chính xác xác suất bộ bài đang cầm là Bất bại (`P_boss`) trên các lá chưa lộ.
    4. Định lý Về Đích 2-Combo (2-Combo Endgame Theorem):
       - Nếu trên tay còn 2 bộ bài `(A, B)` mà `A` là bộ Boss (hoặc xác suất giữ cái > 85%)
         và `B` không phải là quân 2: Đánh `A` cướp cái rồi hạ `B` thắng tuyệt đối 100%!
       - Ngược lại nếu trên tay có quân `2` + 1 bộ khác: Bắt buộc đánh quân `2` TRƯỚC khi còn
         bộ kia trên tay để tuyệt đối không bao giờ phạm luật "Về nhất bằng 2 đền 15 lá"!
    5. Luật Giữ Cửa & Chống Cóng Chủ Động:
       - Khi nhà kế tiếp còn 1–2 lá, tự động đẩy trần phòng thủ, ép đánh bộ nhiều lá hoặc
         đánh cây lẻ cao nhất để khóa đường về của nhà dưới.
    6. Tối ưu hóa Bellman Regret giữa Đánh (`Play`) và Nhường vòng (`Pass`).
    """

    # [V4.6 thử theo profile] LUẬT TESTER (29/10): được đi thì xả loại rác nhiều nhất (lẻ/đôi) từ nhỏ, giữ bộ đỡ;
    # không dùng ĐÔI 2 đè đôi thường trừ khi về luôn / đối thủ <= 2 lá / mình <= 4 lá. Mặc định TẮT.
    tester_rule = False
    # [V4.6.1] bản hẹp: "giu_sanh" = được đi, < 8 lá, nước gốc là SẢNH mà còn >= 2 lá rác lẻ -> đánh rác nhỏ nhất, giữ sảnh làm bộ đỡ;
    # "giu_sanh_all" = như trên nhưng mọi giai đoạn (cần >= 3 lá rác khi >= 8 lá). "" = tắt.
    tester_mode = ""
    rule_set = "full"   # [V4.9.13 A/B] "full" = đủ luật V4.8-V4.9.12 | "chon_loc" = bỏ nhóm luật "giữ heo đánh rác" (đo trên log thật kém), để Monte Carlo

    def __init__(self, name: str = "SamSmartMathBot", xin_sam_max_risk_pct: float = 10.0):
        super().__init__(name=name, xin_sam_max_risk_pct=xin_sam_max_risk_pct)

    def choose_move(self, state: SamTableState) -> SamCombo:
        return self._choose_move_core(state)

    def _choose_move_core(self, state: SamTableState) -> SamCombo:
        self.last_candidates: List[Tuple[float, SamCombo]] = []
        legal = get_legal_sam_moves(
            state.my_hand,
            state.board_combo,
            state.next_player_card_count,
            strict_bao_mot=True,
        )
        non_pass = [m for m in legal if not m.is_pass]
        if not non_pass:
            return PASS_COMBO
        if len(legal) == 1:
            return legal[0]

        # ------------------------------------------------------------------
        # TRƯỜNG HỢP 1: CHÍNH BOT ĐANG BÁO SÂM (XIN SÂM)
        # ------------------------------------------------------------------
        if state.xin_sam_player == state.my_seat:
            if not self._xin_sam_plan:
                self._xin_sam_plan = list(
                    evaluate_xin_sam(
                        hand=state.my_hand,
                        num_players=state.num_players,
                        max_risk_percent=100.0,
                    ).planned_sequence
                )
            hand_set = set(state.my_hand)
            for planned_mv in self._xin_sam_plan:
                if all(c in hand_set for c in planned_mv.cards) and planned_mv in non_pass:
                    return planned_mv

        # ------------------------------------------------------------------
        # TRƯỜNG HỢP 2: ĐỐI THỦ ĐANG BÁO SÂM -> CHẾ ĐỘ "BẮT SÂM" (+20*(N-1) LÁ!)
        # ------------------------------------------------------------------
        if state.xin_sam_player is not None and state.xin_sam_player != state.my_seat:
            # Nếu chặn được bất kỳ nước nào của người Báo Sâm -> Thắng ngay 20*(N-1) lá!
            return max(non_pass, key=lambda m: (m.order_value, m.length))

        # ------------------------------------------------------------------
        # TRƯỜNG HỢP 3: NƯỚC ĐI KẾT THÚC VÁN BÀI NGAY LẬP TỨC (INSTANT WIN)
        # ------------------------------------------------------------------
        for m in non_pass:
            if m.length == len(state.my_hand) and not m.is_all_twos:
                return m

        # ------------------------------------------------------------------
        # TRƯỜNG HỢP 4: PHÂN TÍCH KHÔNG GIAN BÀI CHƯA LỘ & QUY HOẠCH ĐỘNG
        # ------------------------------------------------------------------
        known_cards = set(state.my_hand) | set(state.played_cards)
        unseen_cards = [c for c in range(52) if c not in known_cards]
        unseen_ranks = Counter(card_rank(c) for c in unseen_cards)
        active_opp_counts = [
            state.cards_left[s]
            for s in range(state.num_players)
            if s != state.my_seat and state.cards_left[s] > 0
        ]
        active_opponents = len(active_opp_counts)
        max_opp_cards = max(active_opp_counts) if active_opp_counts else 1

        current_plan = optimal_partition_sam_hand(state.my_hand, unseen_cards)
        plan_combo_cards = {cb.cards for cb in current_plan.combos}
        is_leading = (state.board_combo is None or state.board_combo.is_pass)
        min_opp = state.min_opponent_cards
        next_cnt = state.next_player_card_count
        pass_caps = _extract_sam_opp_pass_caps(state)
        eff_unseen_twos = 0 if pass_caps.get("all_opps_no_two") else unseen_ranks.get(RANK_2, 0)

        # ------------------------------------------------------------------
        # TRƯỜNG HỢP 5: HÀM GIÁ TRỊ TOÁN HỌC LIÊN TỤC (PURE DP + HYPERGEOMETRIC)
        # ------------------------------------------------------------------
        threat_urg = 1.0 / float(max(1, min_opp))
        opp_midgame_urgency = max(0.0, (7.0 - float(min_opp)) / 5.0)
        my_twos_before = sum(1 for c in state.my_hand if card_rank(c) == RANK_2)
        has_normal_resp = any(
            not m_cand.is_pass and not m_cand.is_all_twos and not would_leave_only_twos(state.my_hand, m_cand)
            for m_cand in non_pass
        )
        has_safe_multi_lead_sam = is_leading and any(
            not m_cand.is_pass and m_cand.length >= 2 and not would_leave_only_twos(state.my_hand, m_cand)
            for m_cand in non_pass
        )
        max_single_ord_sam = max(
            (m_cand.order_value for m_cand in non_pass if m_cand.combo_type == SamComboType.SINGLE and not would_leave_only_twos(state.my_hand, m_cand)),
            default=max((m_cand.order_value for m_cand in non_pass if m_cand.combo_type == SamComboType.SINGLE), default=-1),
        )

        best_move = non_pass[0]
        best_utility = -1e18

        for m in legal:
            if m.is_pass:
                if is_leading or state.board_combo is None or (min_opp == 1 and non_pass):
                    utility = -1e9
                else:
                    board_p_beat = _analytic_single_move_beaten_prob(
                        state.board_combo, unseen_ranks, active_opponents,
                        opp_hand_size=max_opp_cards, pass_caps=pass_caps,
                    )
                    pass_risk = (
                        14.0
                        + 18.0 * threat_urg
                        + (120.0 if min_opp == 1 else 0.0)
                        + my_twos_before * 10.0 * (0.38 + 1.55 * threat_urg + 0.95 * opp_midgame_urgency)
                        + (1.0 - board_p_beat) * 6.0
                    )
                    utility = current_plan.total_score - pass_risk
            else:
                if would_leave_only_twos(state.my_hand, m):
                    utility = -1e9
                else:
                    rem_hand = [c for c in state.my_hand if c not in m.cards]
                    rem_plan = optimal_partition_sam_hand(rem_hand, unseen_cards)
                    is_in_plan = (m.cards in plan_combo_cards)

                    my_aces_before = sum(1 for c in state.my_hand if card_rank(c) == RANK_A)
                    rem_aces = sum(1 for c in rem_hand if card_rank(c) == RANK_A)
                    rem_twos = sum(1 for c in rem_hand if card_rank(c) == RANK_2)
                    rem_non2_single_ords = [
                        cb.order_value for cb in rem_plan.combos
                        if cb.combo_type == SamComboType.SINGLE and not cb.is_all_twos
                    ]
                    max_rem_non2_single = max(rem_non2_single_ords, default=-1)
                    strips_last_ace_shield = (
                        is_leading
                        and m.length >= 2
                        and my_aces_before >= 1
                        and rem_aces == 0
                        and (
                            (
                                my_twos_before == 1
                                and rem_twos == 1
                                and eff_unseen_twos >= 1
                                and len(rem_non2_single_ords) >= 3
                                and max_rem_non2_single <= RANK_10
                                and rem_plan.num_turns >= 5
                            )
                            or (
                                rem_twos == 0
                                and min_opp >= 6
                                and rem_plan.num_turns >= 2
                                and all(cb.order_value <= RANK_10 and not is_boss_sam_combo(cb, unseen_cards) for cb in rem_plan.combos)
                            )
                        )
                    )
                    is_ace_preserving_substraight = (
                        is_leading
                        and not is_in_plan
                        and m.combo_type == SamComboType.STRAIGHT
                        and not m.contains_two
                        and m.order_value == straight_max_order_value(m.length) - 1
                        and my_twos_before == 1
                        and my_aces_before == 1
                        and rem_aces == 1
                        and rem_twos == 1
                        and eff_unseen_twos >= 1
                        and len(rem_non2_single_ords) >= 4
                        and any(
                            cb.combo_type == SamComboType.STRAIGHT
                            and cb.length == m.length + 1
                            and set(m.cards).issubset(set(cb.cards))
                            for cb in current_plan.combos
                        )
                    )
                    is_in_plan_eff = is_in_plan or is_ace_preserving_substraight

                    p_beaten = _analytic_single_move_beaten_prob(
                        m, unseen_ranks, active_opponents,
                        opp_hand_size=max_opp_cards, pass_caps=pass_caps,
                    )
                    p_win_trick = 1.0 - p_beaten

                    # 1. Giá trị cấu trúc DP (khấu trừ phần giảm nhịp ảo nếu m là sảnh A-2-3 / 2-3-4 đã bị DP bác bỏ)
                    raw_turn_diff = (current_plan.num_turns - 1) - rem_plan.num_turns
                    delta_turns = 0 if is_ace_preserving_substraight else min(0, raw_turn_diff)
                    rejected_group_pen = max(0, raw_turn_diff) * 32.0 if not is_in_plan_eff else 0.0
                    if rem_plan.num_turns == 1 and not rem_plan.only_twos_end_risk:
                        # Khi chỉ còn 1 bộ cuối cùng: nếu nước m thắng vòng (p_win_trick), ta hạ bộ cuối về đích ngay (điểm cấu trúc = 100.0)
                        eff_rem_score = p_win_trick * 100.0 + (1.0 - p_win_trick) * rem_plan.total_score
                    elif is_in_plan_eff and m.length >= 2 and not m.contains_two:
                        # Khi đánh bộ đa lá thường (Sảnh/Đôi/Sám không chứa 2) nằm trong current_plan,
                        # hoàn lại đúng phần power_bonus của bộ đó để rem_plan.total_score không phạt việc xả bộ!
                        if m.combo_type == SamComboType.STRAIGHT and m.order_value >= 2:
                            _rel_s = m.order_value / max(1, straight_max_order_value(m.length))
                            m_pb = 3.2 + m.length * 1.35 + _rel_s * 3.5 + max(0, m.length - 4) * 8.5
                            if is_boss_sam_combo(m, unseen_cards):
                                m_pb += 5.0
                            if is_leading and not strips_last_ace_shield:
                                m_pb += 12.0 + p_win_trick * 10.0
                            if is_ace_preserving_substraight:
                                m_pb += 26.0
                        elif m.combo_type == SamComboType.TRIPLE:
                            m_pb = (6.8 + m.order_value * 0.45) * p_win_trick
                            if is_leading and not strips_last_ace_shield and (m.order_value >= RANK_8 or current_plan.num_turns <= 4):
                                m_pb += 12.0 + p_win_trick * 10.0
                        elif m.combo_type == SamComboType.PAIR and m.order_value < RANK_K:
                            m_pb = (2.2 + m.order_value * 0.22) * (0.85 if is_leading else 0.5)
                            if is_leading and my_twos_before == 0 and my_aces_before == 0 and rem_plan.num_turns <= 3:
                                m_pb += 12.0 + p_win_trick * 8.0
                        else:
                            m_pb = 0.0
                        eff_rem_score = rem_plan.total_score + m_pb
                    else:
                        eff_rem_score = rem_plan.total_score
                    has_smaller_same_sam = (
                        m.combo_type != SamComboType.SINGLE
                        and any(
                            cb.combo_type == m.combo_type
                            and cb.length == m.length
                            and cb.order_value < m.order_value
                            and not cb.is_all_twos
                            for cb in current_plan.combos
                        )
                    )
                    free_boss_combo_bonus = (
                        (1.0 - p_beaten * 8.0) * (14.0 + m.length * 3.5)
                        + (24.0 if (my_twos_before == 0 and current_plan.num_turns <= 3 and min_opp <= 5) else 0.0)
                        if (is_leading and is_in_plan_eff and not strips_last_ace_shield and m.length >= 2 and not m.contains_two and p_beaten <= 0.10 and not has_smaller_same_sam)
                        else 0.0
                    )
                    armor_strip_pen = 52.0 if strips_last_ace_shield else 0.0
                    structural_ev = (
                        eff_rem_score * 1.15
                        - rejected_group_pen
                        - armor_strip_pen
                        + delta_turns * 24.0
                        + (6.0 if is_in_plan_eff else -7.5)
                        + m.length * (4.5 if is_leading else 3.2)
                        + free_boss_combo_bonus
                    )

                    # 2. Xác suất thu hồi cái có điều kiện (Conditional Recapture under Equal-2 Rule)
                    higher_same_type = [
                        cb for cb in rem_plan.combos
                        if cb.combo_type == m.combo_type and cb.length == m.length and cb.order_value > m.order_value
                    ]
                    if m.combo_type == SamComboType.PAIR and sum(1 for c in rem_hand if card_rank(c) == RANK_2) >= 2 and m.order_value < RANK_2:
                        two_cards = tuple(sorted(c for c in rem_hand if card_rank(c) == RANK_2)[:2])
                        higher_same_type.append(SamCombo(SamComboType.PAIR, two_cards, 2, RANK_2, "Đôi 2"))

                    p_recap = 0.0
                    if higher_same_type:
                        top_same = max(higher_same_type, key=lambda g: g.order_value)
                        p_beat_top = _analytic_single_move_beaten_prob(
                            top_same, unseen_ranks, active_opponents,
                            opp_hand_size=max_opp_cards, pass_caps=pass_caps,
                        )
                        raw_recap = 1.0 - p_beat_top
                        # Trong Sâm Lốc: 2 không đè được 2! Nếu m là Lẻ và top_same là Lẻ 2:
                        # Lẻ 2 chỉ thu hồi được cái nếu đối thủ đè m bằng quân thường (< 2) và không nhảy 2.
                        if m.combo_type == SamComboType.SINGLE and top_same.order_value == RANK_2:
                            if m.order_value >= RANK_A:
                                p_recap = 0.0
                            else:
                                has_ace_bridge = any(cb.order_value == RANK_A for cb in higher_same_type)
                                has_plan_straight = any(
                                    cb.combo_type == SamComboType.STRAIGHT and cb.order_value >= 2
                                    for cb in rem_plan.combos
                                )
                                u_non2 = sum(unseen_ranks.get(r, 0) for r in range(m.order_value + 1, RANK_2))
                                u_2 = eff_unseen_twos
                                bridge_mult = 0.45 if (has_ace_bridge and min_opp >= 6) else (2.5 if (is_leading and has_plan_straight and not has_ace_bridge) else 1.0)
                                p_recap = raw_recap * (
                                    float(u_non2)
                                    / max(1.0, float(u_non2) + float(u_2) * bridge_mult * (1.8 + 12.0 * threat_urg + 6.0 * opp_midgame_urgency))
                                )
                                if is_leading and has_plan_straight and not has_ace_bridge:
                                    p_recap *= 0.40
                        elif m.combo_type == SamComboType.STRAIGHT:
                            max_s_ord = straight_max_order_value(m.length)
                            between_ords = max(0, top_same.order_value - m.order_value - 1)
                            above_ords = max(1, max_s_ord - m.order_value)
                            p_recap = raw_recap * (float(between_ords) / float(above_ords)) * 0.45
                        elif m.combo_type == SamComboType.SINGLE and top_same.order_value <= RANK_10:
                            p_recap = raw_recap * 0.20
                        else:
                            p_recap = raw_recap
                    if active_opponents == 1 and min_opp == m.length:
                        # Trong Solo 1v1: nếu đối thủ còn đúng L lá bằng độ dài nước đi m, đối thủ đè được m là hết bài về nhất luôn (0% cơ hội thu hồi cái)!
                        p_recap = 0.0

                    effective_control = p_win_trick + (1.0 - p_win_trick) * p_recap * (0.85 if is_leading else 0.55)
                    chain_bonus = (
                        p_recap * (11.5 + 5.0 * min(len(higher_same_type), 3))
                        if (is_leading and m.combo_type != SamComboType.STRAIGHT)
                        else (p_recap * (6.0 + 4.5 * min(len(higher_same_type), 3)))
                    )
                    tempo_ev = effective_control * (15.0 + 25.0 * threat_urg) + chain_bonus

                    # 2b. Định lý về đích 2 nhịp liên tục (khi rem_plan.num_turns == 1 và không thối 2 cuối, hoặc num_turns == 2 có bộ cầu bất bại)
                    if rem_plan.num_turns == 1 and not rem_plan.only_twos_end_risk and rem_plan.combos:
                        rem_cb = rem_plan.combos[0]
                        p_beat_last = _analytic_single_move_beaten_prob(
                            rem_cb, unseen_ranks, active_opponents,
                            opp_hand_size=max_opp_cards, pass_caps=pass_caps,
                        )
                        p_two_step_win = p_win_trick + (1.0 - p_win_trick) * (1.0 - p_beat_last) * 0.65
                        tempo_ev += p_two_step_win * 75.0
                    elif (
                        rem_plan.num_turns == 2
                        and not rem_plan.only_twos_end_risk
                        and len(rem_plan.combos) == 2
                        and (
                            (not is_leading and min_opp <= 3)
                            or (
                                is_leading
                                and m.length >= 2
                                and not m.contains_two
                                and (rem_aces >= 1 or (sum(1 for c in rem_hand if card_rank(c) == RANK_2) >= 1 and min_opp >= 4))
                            )
                        )
                    ):
                        cb0, cb1 = rem_plan.combos[0], rem_plan.combos[1]
                        p_b0 = _analytic_single_move_beaten_prob(
                            cb0, unseen_ranks, active_opponents,
                            opp_hand_size=max_opp_cards, pass_caps=pass_caps,
                        )
                        p_b1 = _analytic_single_move_beaten_prob(
                            cb1, unseen_ranks, active_opponents,
                            opp_hand_size=max_opp_cards, pass_caps=pass_caps,
                        )
                        bridge_w = 58.0 if not is_leading else 48.0
                        if p_b0 <= 0.03 and not cb1.is_all_twos:
                            tempo_ev += (p_win_trick + (0.35 if is_leading else 0.0) * (1.0 - p_win_trick)) * (1.0 - p_b0) * bridge_w
                        elif p_b1 <= 0.03 and not cb0.is_all_twos:
                            tempo_ev += (p_win_trick + (0.35 if is_leading else 0.0) * (1.0 - p_win_trick)) * (1.0 - p_b1) * bridge_w

                    # 3. Chi phí tiêu hao tài nguyên kiểm soát (tính theo giai đoạn ván bài & tỷ lệ nhịp)
                    p_opp_finishes_first = min(1.0, max(0.05, (float(rem_plan.num_turns) / max(1.0, float(min_opp) + 0.3)) ** 1.35))
                    calm = max(0.0, min(1.0 - p_opp_finishes_first * 0.55, (float(min_opp) - 5.0) / 3.5))
                    max_ord = float(max(
                        1,
                        straight_max_order_value(m.length) if m.combo_type == SamComboType.STRAIGHT else RANK_2
                    ))
                    ord_norm = float(m.order_value) / max_ord
                    twos_used = sum(1 for c in m.cards if card_rank(c) == RANK_2)
                    non_term = min(1.0, max(0.0, float(rem_plan.num_turns - 1) / 3.0))
                    # Bảo vệ Đôi 2 ở đầu ván (calm > 0) khi trên tay có Đôi thường cần Đôi 2 bọc hoặc đã có Át canh đường lẻ;
                    # ngược lại nếu cầm toàn bài lẻ không có Át và không có đôi thường nào (như [8♣ 9♦ Q♦ K♠ 2♠ 2♥]), giữ Đôi 2 sẽ bị kẹt Thối Đôi 2!
                    has_other_pair_sam = any(
                        cb.combo_type == SamComboType.PAIR and not cb.is_all_twos
                        for cb in current_plan.combos
                    )
                    has_ace_sam = any(card_rank(c) == RANK_A for c in state.my_hand)
                    non2_singles_in_plan = sum(
                        1 for cb in current_plan.combos
                        if cb.combo_type == SamComboType.SINGLE and not cb.is_all_twos
                    )
                    no_pair_no_ace_two_trap = (
                        my_twos_before >= 2
                        and not has_other_pair_sam
                        and not has_ace_sam
                        and non2_singles_in_plan >= 3
                    )
                    split_pair2_cost = (
                        (48.0 * max(0.65, calm))
                        if (my_twos_before >= 2 and twos_used == 1 and (is_leading or has_normal_resp) and not no_pair_no_ace_two_trap)
                        else 0.0
                    )
                    ord_ctrl_weight = 0.0 if (is_leading and m.combo_type == SamComboType.STRAIGHT and not m.contains_two) else (12.5 if not is_leading else 8.5)

                    same_type_order_pen = 0.0
                    high_guard_burn_pen = 0.0
                    single_2_channel_pen = 0.0
                    if is_leading and min_opp > 1 and rem_plan.num_turns >= 2 and twos_used == 0:
                        if m.combo_type != SamComboType.SINGLE:
                            has_smaller_same_sam = any(
                                cb.combo_type == m.combo_type
                                and cb.length == m.length
                                and cb.order_value < m.order_value
                                and not cb.is_all_twos
                                for cb in current_plan.combos
                            )
                            if has_smaller_same_sam and not (rem_plan.num_turns == 1 and not rem_plan.only_twos_end_risk and p_beaten <= 0.02):
                                same_type_order_pen = 28.0
                        else:
                            has_smaller_single_sam = any(
                                cb.combo_type == SamComboType.SINGLE
                                and cb.order_value < m.order_value
                                and not cb.is_all_twos
                                for cb in current_plan.combos
                            )
                            if has_smaller_single_sam:
                                same_type_order_pen = 11.0

                        if (
                            m.combo_type in (SamComboType.PAIR, SamComboType.TRIPLE)
                            and m.order_value >= RANK_Q
                            and not higher_same_type
                            and min_opp >= 4
                            and rem_plan.num_turns >= 3
                        ):
                            has_plan_st = any(cb.combo_type == SamComboType.STRAIGHT and cb.order_value >= 2 for cb in current_plan.combos)
                            if has_plan_st or rem_plan.trash_count >= 2:
                                high_guard_burn_pen = 22.0 * max(0.45, calm)

                        if (
                            m.combo_type == SamComboType.PAIR
                            and m.order_value <= RANK_10
                            and p_recap < 0.45
                            and my_twos_before >= 1
                            and current_plan.trash_count >= 1
                            and (rem_plan.num_turns >= 3 or min_opp <= 3)
                            and not any(cb.combo_type == SamComboType.STRAIGHT and cb.length >= 4 for cb in current_plan.combos)
                        ):
                            single_2_channel_pen = 18.0

                    # Quy tắc Bài Tròn <= 4 nhịp có Heo lẻ và Sảnh/Bộ có thể bị chặn (vd [5-6-7, 9-10-J, A♠, 2♥] hoặc [44, 6-7-8, 99, 2♣]):
                    # Trong Sâm Lốc 2 không được đánh cuối cùng -> Khi bài tròn không còn rác lẻ (trash_count == 0) và tổng <= 4 nhịp,
                    # bắt buộc xả 2 lẻ trước khi đang cầm cái để giữ cái ~99.5% và triệt tiêu hoàn toàn rủi ro Thối 2!
                    round_hand_two_first_ev = 0.0
                    has_boss_multi_in_plan = any(
                        cb.length >= 2 and not cb.is_all_twos and is_boss_sam_combo(cb, unseen_cards)
                        for cb in current_plan.combos
                    )
                    if is_leading and my_twos_before >= 1 and not rem_plan.only_twos_end_risk:
                        non2_multis_in_plan = [
                            cb for cb in current_plan.combos
                            if cb.length >= 2 and not cb.is_all_twos
                        ]
                        if (
                            current_plan.num_turns <= 4
                            and (
                                rem_plan.num_turns == 1
                                or (non2_singles_in_plan == 0 and non2_multis_in_plan and my_twos_before == 1)
                            )
                        ):
                            if m.is_all_twos and m.combo_type == SamComboType.SINGLE:
                                round_hand_two_first_ev = 42.0
                            elif m.length >= 2 and my_twos_before == sum(1 for c in rem_hand if card_rank(c) == RANK_2):
                                round_hand_two_first_ev = -24.0 * max(0.35, p_beaten)
                        elif min_opp in (2, 3) and not has_boss_multi_in_plan and eff_unseen_twos >= 1:
                            if m.is_all_twos:
                                round_hand_two_first_ev = 34.0 * float(twos_used)
                            elif p_beaten > 0.20:
                                round_hand_two_first_ev = -18.0 * float(my_twos_before) * p_beaten

                    cur_non2_single_ords = [
                        cb.order_value for cb in current_plan.combos
                        if cb.combo_type == SamComboType.SINGLE and not cb.is_all_twos
                    ]
                    no_ace_single_two_lock_trap = (
                        my_twos_before == 1
                        and not has_ace_sam
                        and eff_unseen_twos >= 1
                        and max(cur_non2_single_ords, default=-1) <= RANK_10
                        and len(cur_non2_single_ords) >= 2
                        and len(state.my_hand) <= 6
                    )
                    control_cost = (
                        ord_norm * ord_ctrl_weight * calm
                        + float(twos_used) * (24.0 if (not is_leading and has_normal_resp and not no_pair_no_ace_two_trap and not no_ace_single_two_lock_trap) else (26.0 if is_leading and round_hand_two_first_ev <= 0.0 else 4.0)) * calm
                        + split_pair2_cost
                        + float(twos_used) * (1.0 - p_win_trick) * 45.0
                    ) * non_term + same_type_order_pen + high_guard_burn_pen + single_2_channel_pen

                    # 4. Kỳ vọng chặt 2, cướp cái giải phóng bộ & Quản trị rủi ro khóa 2 / Thối 2
                    chop_gain = (
                        25.0 * float(state.board_combo.length)
                        if (not is_leading and state.board_combo is not None and state.board_combo.is_all_twos and m.combo_type == SamComboType.FOUR_OF_KIND)
                        else 0.0
                    )
                    p_chop = p_beaten if m.is_all_twos else 0.0
                    expected_chop_loss = p_chop * 22.0 * float(m.length)

                    my_twos_after = sum(1 for c in rem_hand if card_rank(c) == RANK_2)
                    twos_shed = float(my_twos_before - my_twos_after)
                    n_multi_rem = sum(1 for cb in rem_plan.combos if cb.length >= 2 and not cb.is_all_twos)

                    # Khi đang phải đỡ bài và đối thủ đã xuống <= 8 lá (opp_midgame_urgency > 0) hoặc không còn quân thường đỡ:
                    # Đánh 2 cướp cái chắc chắn (~99.6%) giúp bù lại 24đ giữ Boss ảo của DP, xóa 10 lá phạt thối 2,
                    # thoát Cóng (khi còn 10 lá) và mở khóa các bộ đa lá đang chờ trên tay.
                    eff_midgame_urg = max(
                        opp_midgame_urgency,
                        0.42 if (not is_leading and min_opp <= 8 and state.board_combo is not None and state.board_combo.order_value >= RANK_8 and (n_multi_rem >= 1 or current_plan.num_turns >= 5)) else 0.0,
                        0.68 if (not is_leading and no_pair_no_ace_two_trap) else 0.0,
                        0.72 if (not is_leading and no_ace_single_two_lock_trap) else 0.0,
                    )
                    seize_lead_2_ev = 0.0
                    if not is_leading and twos_shed > 0 and not m.combo_type == SamComboType.STRAIGHT and (eff_midgame_urg > 0.0 or not has_normal_resp):
                        seize_lead_2_ev = p_win_trick * (
                            twos_shed * 26.0 * (eff_midgame_urg + 0.5 * p_opp_finishes_first)
                            + 9.5 * float(n_multi_rem) * eff_midgame_urg
                            + (18.0 * eff_midgame_urg if len(state.my_hand) == 10 else 0.0)
                            + (22.0 if rem_plan.num_turns <= 3 and min_opp <= 6 else 0.0)
                            + (55.0 if no_pair_no_ace_two_trap and twos_used == 1 else 0.0)
                            + (42.0 if no_ace_single_two_lock_trap and twos_used == 1 else 0.0)
                        )

                    # Xác suất bị đối thủ đè 2 khóa cửa (trong Sâm 2 không đè được 2)
                    lockout_prob = (1.0 - effective_control)
                    if not is_leading and my_twos_after > 0 and eff_unseen_twos > 0:
                        lockout_prob = min(1.0, lockout_prob + 0.45 * eff_midgame_urg)

                    early_single2_calm = (
                        0.0
                        if (is_leading and min_opp >= 6 and rem_plan.num_turns >= 3 and round_hand_two_first_ev <= 0.0)
                        else (0.30 if (min_opp >= 9 and my_twos_before == 1 and has_normal_resp and not no_ace_single_two_lock_trap) else 1.0)
                    )
                    thoi2_ev = early_single2_calm * (
                        twos_shed * 10.0 * (p_opp_finishes_first * 1.45 + 2.2 * threat_urg + 1.25 * eff_midgame_urg)
                        - float(my_twos_after) * 10.0 * lockout_prob * (0.35 + 1.55 * threat_urg + 1.35 * eff_midgame_urg)
                    ) + seize_lead_2_ev + round_hand_two_first_ev

                    # 5. Chặn cửa khi có đối thủ báo 1 lá (Tuyệt đối không mở lẻ yếu khi có bộ đa lá an toàn)
                    anti_bao1_ev = 0.0
                    if min_opp == 1:
                        if is_leading:
                            if m.length >= 2:
                                anti_bao1_ev = (64.0 if is_in_plan else 46.0) + m.length * 4.5
                            elif rem_plan.num_turns == 1 and not rem_plan.only_twos_end_risk and p_beaten <= 1e-6:
                                anti_bao1_ev = 70.0
                            elif has_safe_multi_lead_sam:
                                anti_bao1_ev = -65.0 + ord_norm * 10.0
                            else:
                                if m.order_value == max_single_ord_sam:
                                    anti_bao1_ev = 55.0 + p_win_trick * 25.0
                                else:
                                    anti_bao1_ev = -65.0 + ord_norm * 12.0
                        else:
                            if m.combo_type == SamComboType.SINGLE:
                                anti_bao1_ev = (
                                    p_win_trick * 48.0
                                    + ord_norm * 24.0
                                    + (18.0 if m.order_value == max_single_ord_sam else 0.0)
                                )
                            else:
                                anti_bao1_ev = p_win_trick * 48.0 + m.length * 5.0

                    utility = (
                        structural_ev
                        + tempo_ev
                        - control_cost
                        + chop_gain
                        - expected_chop_loss
                        + thoi2_ev
                        + anti_bao1_ev
                    )

            self.last_candidates.append((utility, m))
            if utility > best_utility:
                best_utility = utility
                best_move = m

        self.last_candidates.sort(key=lambda x: -x[0])
        return best_move

# ============================================================================
# 6. BỘ MÔ PHỎNG VÁN ĐẤU SÂM LỐC CHUẨN LUẬT SUN.WIN & DUPLICATE BENCHMARK
# ============================================================================

@dataclass
class SamHandResult:
    winner_seat: int
    xin_sam_seat: Optional[int]
    xin_sam_success: Optional[bool]
    card_deltas: List[int]           # Số lá thắng/thua của từng vị trí (Tổng bằng 0)
    chopped_twos_bonus: List[int]    # Điểm thưởng/phạt chặt 2 trong ván
    summary: str


def simulate_sam_hand(
    bots: Sequence[BaseSamBot],
    hands: Sequence[Sequence[int]],
    starting_seat: int = 0,
    allow_xin_sam: bool = True,
) -> SamHandResult:
    """
    Mô phỏng 1 ván Sâm Lốc chuẩn luật SUN.WIN:
    - Kiểm tra Báo Sâm (Xin Sâm) đầu ván.
    - Thực thi đánh bài theo vòng, kiểm tra Chặt 2 (10 lá/con), Cóng (15 lá + hàng thối),
      Thối 2 (10 lá/con), Thối Tứ quý (10 lá/bộ), Đền Báo 1 (15 lá).
    """
    num_players = len(bots)
    cur_hands: List[List[int]] = [sorted(list(h)) for h in hands]
    initial_counts = [len(h) for h in cur_hands]
    played_cards: List[int] = []
    history: List[Tuple[int, SamCombo]] = []
    chop_deltas = [0] * num_players

    for b in bots:
        b.reset_for_new_hand()

    # 1. GIAI ĐOẠN BÁO SÂM (XIN SÂM) ĐẦU VÁN
    xin_sam_seat: Optional[int] = None
    if allow_xin_sam:
        for offset in range(num_players):
            seat = (starting_seat + offset) % num_players
            analysis = bots[seat].decide_xin_sam(cur_hands[seat], num_players)
            if analysis.should_declare:
                xin_sam_seat = seat
                break

    # Nếu có người Báo Sâm: Người đó giành cái đánh liên tục, nếu bị bất kỳ ai chặn -> Đền Sâm ngay!
    if xin_sam_seat is not None:
        sam_seat = xin_sam_seat
        while cur_hands[sam_seat]:
            state = SamTableState(
                num_players=num_players,
                my_seat=sam_seat,
                my_hand=list(cur_hands[sam_seat]),
                board_combo=None,
                board_owner=None,
                cards_left=[len(h) for h in cur_hands],
                played_cards=list(played_cards),
                passed_in_round=[False] * num_players,
                xin_sam_player=sam_seat,
                history=list(history),
            )
            move = bots[sam_seat].choose_move(state)
            if move.is_pass or not all(c in cur_hands[sam_seat] for c in move.cards):
                # Lỗi nước đi -> xử thua Đền Sâm
                legal = get_legal_sam_moves(cur_hands[sam_seat], None, 10, False)
                move = legal[0]

            for c in move.cards:
                cur_hands[sam_seat].remove(c)
                played_cards.append(c)
            history.append((sam_seat, move))

            # Kiểm tra nếu đây là nước cuối cùng (hết bài):
            if not cur_hands[sam_seat]:
                if move.is_all_twos:
                    # Về nhất bằng 2 khi Báo Sâm -> Đền Sâm!
                    penalty = ACTIVE_SAM_RULE.bao_sam * (num_players - 1)
                    deltas = [0] * num_players
                    deltas[sam_seat] = -penalty
                    other_share = penalty // (num_players - 1)
                    for s in range(num_players):
                        if s != sam_seat:
                            deltas[s] = other_share
                    return SamHandResult(
                        winner_seat=(sam_seat + 1) % num_players,
                        xin_sam_seat=sam_seat,
                        xin_sam_success=False,
                        card_deltas=deltas,
                        chopped_twos_bonus=chop_deltas,
                        summary=f"Seat {sam_seat} ({bots[sam_seat].name}) Báo Sâm nhưng kết thúc bằng 2 -> Đền Sâm!",
                    )
                # Nước cuối hợp lệ và tất cả các nước dẫn trước đó không ai bắt được -> ĂN SÂM!
                win_total = ACTIVE_SAM_RULE.bao_sam * (num_players - 1)
                deltas = [-ACTIVE_SAM_RULE.bao_sam] * num_players
                deltas[sam_seat] = win_total
                return SamHandResult(
                    winner_seat=sam_seat,
                    xin_sam_seat=sam_seat,
                    xin_sam_success=True,
                    card_deltas=deltas,
                    chopped_twos_bonus=chop_deltas,
                    summary=f"Seat {sam_seat} ({bots[sam_seat].name}) ĂN SÂM THÀNH CÔNG (+{win_total} lá)!",
                )

            # Khi người Báo Sâm vẫn còn bài trên tay sau nước `move`, kiểm tra xem có đối thủ nào bắt được không
            for offset in range(1, num_players):
                opp_seat = (sam_seat + offset) % num_players
                opp_legal = get_legal_sam_moves(cur_hands[opp_seat], move, len(cur_hands[sam_seat]), False)
                opp_beating = [m for m in opp_legal if not m.is_pass]
                if opp_beating:
                    # BẮT SÂM THÀNH CÔNG! Ván bài dừng ngay lập tức, người Báo Sâm đền 20*(N-1) lá cho người bắt!
                    penalty = ACTIVE_SAM_RULE.bao_sam * (num_players - 1)
                    deltas = [0] * num_players
                    deltas[sam_seat] = -penalty
                    deltas[opp_seat] = penalty
                    return SamHandResult(
                        winner_seat=opp_seat,
                        xin_sam_seat=sam_seat,
                        xin_sam_success=False,
                        card_deltas=deltas,
                        chopped_twos_bonus=chop_deltas,
                        summary=(
                            f"Seat {sam_seat} ({bots[sam_seat].name}) bị Seat {opp_seat} "
                            f"({bots[opp_seat].name}) BẮT SÂM ở nước {move} (-{penalty} lá)!"
                        ),
                    )

    # 2. GIAI ĐOẠN ĐÁNH BÀI THÔNG THƯỜNG
    current_seat = starting_seat
    board_combo: Optional[SamCombo] = None
    board_owner: Optional[int] = None
    passed = [False] * num_players
    last_chop_event: Optional[Tuple[int, int, int]] = None  # (chopper, victim, amount)
    opp_pass_log_sim: Dict[int, List[Tuple[SamCombo, List[int]]]] = {s: [] for s in range(num_players)}

    max_steps = 400
    step = 0
    winner_seat = starting_seat
    finished_with_two_penalty_seat: Optional[int] = None

    while step < max_steps:
        step += 1
        # Nếu mọi nhà khác đều đã bỏ lượt, người giữ cái trên bàn mở vòng mới
        active_not_passed = [s for s in range(num_players) if not passed[s] and len(cur_hands[s]) > 0]
        if board_owner is not None and (
            len(active_not_passed) <= 1 and current_seat == board_owner
        ):
            # Nếu vòng trước có chặt 2, cộng điểm chặt 2
            if last_chop_event is not None:
                chopper, victim, amt = last_chop_event
                chop_deltas[chopper] += amt
                chop_deltas[victim] -= amt
                last_chop_event = None
            board_combo = None
            board_owner = None
            passed = [False] * num_players

        if passed[current_seat] or len(cur_hands[current_seat]) == 0:
            current_seat = (current_seat + 1) % num_players
            continue

        state = SamTableState(
            num_players=num_players,
            my_seat=current_seat,
            my_hand=list(cur_hands[current_seat]),
            board_combo=board_combo,
            board_owner=board_owner,
            cards_left=[len(h) for h in cur_hands],
            played_cards=list(played_cards),
            passed_in_round=list(passed),
            xin_sam_player=None,
            history=list(history),
            opp_pass_log={
                s: [(bc, tuple(pa)) for bc, pa in entries]
                for s, entries in opp_pass_log_sim.items()
                if s != current_seat and entries
            },
        )
        move = bots[current_seat].choose_move(state)

        # Kiểm tra tính hợp lệ của nước đi
        legal = get_legal_sam_moves(
            cur_hands[current_seat],
            board_combo,
            state.next_player_card_count,
            strict_bao_mot=True,
        )
        if move not in legal:
            # Nếu bot bị kẹt toàn 2 ở lượt cuối, hệ thống buộc phải đánh ra và xử phạt Về bằng 2
            raw_all = generate_all_sam_combos(cur_hands[current_seat])
            raw_beating = (
                raw_all
                if (board_combo is None or board_combo.is_pass)
                else [c for c in raw_all if can_beat_sam(board_combo, c)] + [PASS_COMBO]
            )
            if move in raw_beating:
                pass
            else:
                move = legal[0] if legal else raw_beating[0]

        if move.is_pass:
            passed[current_seat] = True
            if board_combo is not None and not board_combo.is_pass:
                opp_pass_log_sim[current_seat].append((board_combo, []))
        else:
            for _, pa in opp_pass_log_sim[current_seat]:
                pa.extend(move.cards)
            # Kiểm tra chặt 2 bằng Tứ quý
            if (
                board_combo is not None
                and board_combo.combo_type == SamComboType.SINGLE
                and board_combo.order_value == RANK_2
                and move.combo_type == SamComboType.FOUR_OF_KIND
                and board_owner is not None
            ):
                last_chop_event = (current_seat, board_owner, ACTIVE_SAM_RULE.chop_two)
            elif (
                board_combo is not None
                and board_combo.combo_type == SamComboType.FOUR_OF_KIND
                and move.combo_type == SamComboType.FOUR_OF_KIND
                and last_chop_event is not None
            ):
                # Tứ quý lớn hơn đè Tứ quý trước
                _, orig_victim, amt = last_chop_event
                last_chop_event = (current_seat, orig_victim, amt)

            for c in move.cards:
                cur_hands[current_seat].remove(c)
                played_cards.append(c)

            board_combo = move
            board_owner = current_seat
            history.append((current_seat, move))

            # Kiểm tra kết thúc ván bài (1 nhà hết bài)
            if len(cur_hands[current_seat]) == 0:
                if last_chop_event is not None:
                    chopper, victim, amt = last_chop_event
                    chop_deltas[chopper] += amt
                    chop_deltas[victim] -= amt
                    last_chop_event = None

                if move.is_all_twos:
                    # Phạm luật "Về nhất bằng 2 đền 15 lá"!
                    finished_with_two_penalty_seat = current_seat
                winner_seat = current_seat
                break

        current_seat = (current_seat + 1) % num_players

    # 3. TÍNH ĐIỂM THẮNG THUA (QUY ĐỔI RA SỐ LÁ CƯỢC)
    deltas = list(chop_deltas)

    if finished_with_two_penalty_seat is not None:
        # Người về nhất bằng 2 bị phạt đền 15 lá cho mỗi nhà (hoặc đền làng)
        bad_seat = finished_with_two_penalty_seat
        pen = ACTIVE_SAM_RULE.finish_two_penalty * (num_players - 1)
        deltas[bad_seat] -= pen
        for s in range(num_players):
            if s != bad_seat:
                deltas[s] += ACTIVE_SAM_RULE.finish_two_penalty
        return SamHandResult(
            winner_seat=(bad_seat + 1) % num_players,
            xin_sam_seat=None,
            xin_sam_success=None,
            card_deltas=deltas,
            chopped_twos_bonus=chop_deltas,
            summary=f"Seat {bad_seat} phạm luật Về nhất bằng 2 (-{pen} lá)!",
        )

    total_won_by_winner = 0
    for s in range(num_players):
        if s == winner_seat:
            continue
        rem = cur_hands[s]
        rem_cnt = len(rem)
        num_twos = sum(1 for c in rem if card_rank(c) == RANK_2)
        rank_cnts = Counter(card_rank(c) for c in rem)
        num_quads = sum(1 for r, cnt in rank_cnts.items() if cnt == 4)

        if rem_cnt == initial_counts[s]:
            # CÓNG: Phạt 15 lá + Thối 2 (10 lá/con) + Thối Tứ quý (10 lá/bộ)
            loss = ACTIVE_SAM_RULE.cong + num_twos * ACTIVE_SAM_RULE.thoi_two + num_quads * ACTIVE_SAM_RULE.thoi_four
        else:
            # THUA THƯỜNG: Đếm số lá còn lại + Thối 2 (10 lá/con) + Thối Tứ quý (10 lá/bộ)
            loss = rem_cnt + num_twos * ACTIVE_SAM_RULE.thoi_two + num_quads * ACTIVE_SAM_RULE.thoi_four

        deltas[s] -= loss
        total_won_by_winner += loss

    deltas[winner_seat] += total_won_by_winner
    return SamHandResult(
        winner_seat=winner_seat,
        xin_sam_seat=None,
        xin_sam_success=None,
        card_deltas=deltas,
        chopped_twos_bonus=chop_deltas,
        summary=f"Seat {winner_seat} ({bots[winner_seat].name}) về nhất (+{total_won_by_winner} lá).",
    )



# ============================================================================
# 6B. [V2] MONTE CARLO TRÊN BÀI ẨN CHO SÂM LỐC (SamMCBot)
# ============================================================================

def rollout_sam_from_state(
    hands: List[List[int]],
    played_cards: List[int],
    board_combo: Optional[SamCombo],
    board_owner: Optional[int],
    passed: List[bool],
    current_seat: int,
    policies: Sequence["BaseSamBot"],
    initial_counts: Sequence[int],
    rule: Optional[SamRuleConfig] = None,
    max_steps: int = 300,
    chop_event: Optional[Tuple[int, int, int]] = None,
) -> List[int]:
    """Đánh tiếp ván Sâm (giai đoạn đánh thường) từ 1 trạng thái đã biết hết bài, trả về biến động lá từng ghế."""
    cfg = rule or ACTIVE_SAM_RULE
    n = len(hands)
    cur = [list(h) for h in hands]
    played = list(played_cards)
    passed = list(passed)
    deltas = [0] * n
    winner = None
    last_move: Optional[SamCombo] = None
    seat = current_seat
    opp_pass_log_ro: Dict[int, List[Tuple[SamCombo, List[int]]]] = {s: [] for s in range(n)}
    for _ in range(max_steps):
        active_not_passed = [s for s in range(n) if not passed[s] and cur[s]]
        if board_owner is not None and len(active_not_passed) <= 1 and seat == board_owner:
            if chop_event is not None:
                c, v, a = chop_event
                deltas[c] += a
                deltas[v] -= a
                chop_event = None
            board_combo, board_owner, passed = None, None, [False] * n
        if passed[seat] or not cur[seat]:
            seat = (seat + 1) % n
            continue
        state = SamTableState(
            num_players=n, my_seat=seat, my_hand=list(cur[seat]), board_combo=board_combo,
            board_owner=board_owner, cards_left=[len(h) for h in cur], played_cards=list(played),
            passed_in_round=list(passed), xin_sam_player=None,
            opp_pass_log={
                s: [(bc, tuple(pa)) for bc, pa in entries]
                for s, entries in opp_pass_log_ro.items()
                if s != seat and entries
            },
        )
        move = policies[seat].choose_move(state)
        legal = get_legal_sam_moves(cur[seat], board_combo, state.next_player_card_count, strict_bao_mot=True)
        if move not in legal:
            move = legal[0] if legal else PASS_COMBO
        if move.is_pass:
            if board_combo is None:  # không được bỏ lượt khi mở vòng
                alls = generate_all_sam_combos(cur[seat])
                move = min(alls, key=lambda m: (m.order_value, -m.length))
            else:
                passed[seat] = True
                if not board_combo.is_pass:
                    opp_pass_log_ro[seat].append((board_combo, []))
                seat = (seat + 1) % n
                continue
        for _, pa in opp_pass_log_ro[seat]:
            pa.extend(move.cards)
        if (board_combo is not None and board_combo.combo_type == SamComboType.SINGLE
                and board_combo.order_value == RANK_2 and move.combo_type == SamComboType.FOUR_OF_KIND
                and board_owner is not None):
            chop_event = (seat, board_owner, cfg.chop_two)
        elif (board_combo is not None and board_combo.combo_type == SamComboType.FOUR_OF_KIND
              and move.combo_type == SamComboType.FOUR_OF_KIND and chop_event is not None):
            chop_event = (seat, chop_event[1], chop_event[2])
        for c in move.cards:
            cur[seat].remove(c)
            played.append(c)
        board_combo, board_owner, last_move = move, seat, move
        if not cur[seat]:
            winner = seat
            break
        seat = (seat + 1) % n
    if chop_event is not None:
        c, v, a = chop_event
        deltas[c] += a
        deltas[v] -= a
    if winner is None:
        return deltas
    if last_move is not None and last_move.is_all_twos:
        for s in range(n):
            if s != winner:
                deltas[s] += cfg.finish_two_penalty
        deltas[winner] -= cfg.finish_two_penalty * (n - 1)
        return deltas
    total = 0
    for s in range(n):
        if s == winner:
            continue
        rem = cur[s]
        twos = sum(1 for c in rem if card_rank(c) == RANK_2)
        quads = sum(1 for _, k in Counter(card_rank(c) for c in rem).items() if k == 4)
        base = cfg.cong if len(rem) == initial_counts[s] else len(rem)
        loss = base + twos * cfg.thoi_two + quads * cfg.thoi_four
        deltas[s] -= loss
        total += loss
    deltas[winner] += total
    return deltas


class SamNeverPassBot(BaseSamBot):
    """
    [V3] Đối thủ Sâm cổng HIT thật (đo trên 149 ván 27/10/2026): chặn được là chặn (bỏ lượt 2/255 lần),
    dùng Heo chặn 61% số lần có thể. Dẫn bài như SamSmartMathBot; khi phải đáp: nếu SamSmartMathBot muốn bỏ lượt mà có
    nước chặn -> chặn; `cheapest=True` thì chặn bằng nước nhỏ nhất.
    """

    def __init__(self, name: str = "SamNeverPass", cheapest: bool = False):
        super().__init__(name, 10.0)
        self.inner = SamSmartMathBot(name + "_in", 10.0)
        self.cheapest = cheapest

    def reset_for_new_hand(self) -> None:
        super().reset_for_new_hand()
        self.inner.reset_for_new_hand()

    def decide_xin_sam(self, hand: Sequence[int], num_players: int) -> XinSamAnalysis:
        return self.inner.decide_xin_sam(hand, num_players)  # kế hoạch Báo Sâm nằm ở bot bên trong

    def choose_move(self, state: SamTableState) -> SamCombo:
        mv = self.inner.choose_move(state)
        if state.board_combo is None or not mv.is_pass:
            return mv
        beats = [m for m in get_legal_sam_moves(state.my_hand, state.board_combo, state.next_player_card_count) if not m.is_pass]
        if not beats:
            return mv
        if state.next_player_card_count > 3 and len(state.my_hand) >= 4:
            plan = optimal_partition_sam_hand(state.my_hand)
            clean_beats = [
                m for m in beats
                if not would_leave_only_twos(state.my_hand, m)
                and optimal_partition_sam_hand([c for c in state.my_hand if c not in m.cards]).num_turns <= plan.num_turns - 1
            ]
            if not clean_beats:
                return mv
            beats = clean_beats
        if self.cheapest:
            return min(beats, key=lambda m: (len(m.cards), m.order_value))
        beat_set = {tuple(sorted(m.cards)) for m in beats}
        ranked = [
            m for _, m in (getattr(self.inner, "last_candidates", []) or [])
            if not m.is_pass and tuple(sorted(m.cards)) in beat_set
        ]
        return ranked[0] if ranked else min(beats, key=lambda m: (len(m.cards), m.order_value))


# [V4.9.31] XÁC SUẤT BỎ LƯỢT CÓ NHẬN THỨC CẤU TRÚC BÀI (PARTITION-AWARE BAYESIAN PASS LIKELIHOOD):
# Chỉ coi đối thủ có "bộ rảnh" (xác suất bỏ lượt rất thấp 4-8%) khi bộ/lá đó NẰM ĐỘC LẬP trong phân hoạch tối ưu
# `optimal_partition_sam_hand(hand)` và không phải quân 2 / Tứ quý.
# Nếu muốn chặn bàn mà đối thủ buộc phải dùng 2, chặt Tứ quý, hoặc XÉ SẢNH / XÉ ĐÔI / XÉ SÁM thì người thật
# rất hay bỏ lượt (xác suất bỏ lượt 25-60%), tuyệt đối không gán 0.01 làm Monte Carlo tưởng đối thủ đã hết sạch 2 và bài lớn!
def sam_pass_likelihood(hand: Sequence[int], board: SamCombo) -> float:
    """Xác suất người thật bỏ lượt trước `board` khi cầm `hand` (bài lúc bỏ), có xét phân hoạch tối ưu."""
    if board is None or board.is_pass or board.is_all_twos or not hand:
        return 1.0
    t = board.combo_type
    br = board.order_value
    rc = Counter(card_rank(c) for c in hand)
    if t == SamComboType.SINGLE:
        if not any(r > br for r in rc):
            return 1.0
        plan = optimal_partition_sam_hand(hand)
        free_singles = [
            cb.order_value for cb in plan.combos
            if cb.combo_type == SamComboType.SINGLE and not cb.is_all_twos and cb.order_value > br
        ]
        if free_singles:
            return 0.04 if any(r < RANK_A for r in free_singles) else 0.12
        if len(hand) <= 3:
            return 0.15
        if br >= RANK_Q:
            return 0.25
        return 0.60
    if t == SamComboType.PAIR:
        if not any(k >= 2 and r > br for r, k in rc.items()):
            return 1.0
        plan = optimal_partition_sam_hand(hand)
        if any(
            cb.combo_type == SamComboType.PAIR and not cb.is_all_twos and cb.order_value > br
            for cb in plan.combos
        ):
            return 0.05
        return 0.55 if len(hand) >= 5 else 0.25
    if t == SamComboType.TRIPLE:
        if not any(k >= 3 and r > br for r, k in rc.items()):
            return 1.0
        plan = optimal_partition_sam_hand(hand)
        if any(
            cb.combo_type == SamComboType.TRIPLE and not cb.is_all_twos and cb.order_value > br
            for cb in plan.combos
        ):
            return 0.08
        return 0.60
    if t == SamComboType.STRAIGHT:
        beats = [
            m for m in get_legal_sam_moves(hand, board, 10, strict_bao_mot=False)
            if not m.is_pass and m.combo_type == SamComboType.STRAIGHT
        ]
        if not beats:
            return 1.0
        plan = optimal_partition_sam_hand(hand)
        if any(
            cb.combo_type == SamComboType.STRAIGHT
            and cb.length == board.length
            and cb.order_value > br
            and not any(card_rank(c) == RANK_2 for c in cb.cards)
            for cb in plan.combos
        ):
            return 0.05
        return 0.50
    return 1.0


class SamMCBot(SamSmartMathBot):
    """
    [V2] SamSmartMathBot + Monte Carlo trên bài ẩn (giống SmartMCBot của Tiến Lên HIT):
    - Heuristic chấm điểm, lấy `top_k` ứng viên (+ Bỏ lượt nếu hợp lệ).
    - Chia ngẫu nhiên bài chưa lộ cho đối thủ đúng số lá, đánh thử từng ứng viên tới hết ván
      (mình: SamSmartMathBot; đối thủ: ngẫu nhiên 1 trong 5 kiểu nếu `opponent_mix`).
    - Chỉ ghi đè heuristic khi MC hơn > max(min_override_gain, override_z x sai số chuẩn);
      nước sát nút thì lấy thêm mẫu (mỗi lần 8) tới `max_samples`.
    - Không dùng MC khi đang Báo Sâm / bắt Sâm (giữ logic chuyên biệt).
    """

    def __init__(self, name: str = "SamMCBot", xin_sam_max_risk_pct: float = 10.0, samples: int = 32,
                 max_samples: Optional[int] = 96, top_k: int = 6, override_z: float = 1.0,
                 min_override_gain: float = 0.25, opponent_mix: bool = True,
                 time_limit_sec: Optional[float] = None, min_samples: int = 16, seed: Optional[int] = None,
                 opp_pool: str = "hit_real", search_all: bool = True, two_aggr: int = 1):
        super().__init__(name=name, xin_sam_max_risk_pct=xin_sam_max_risk_pct)
        # [V3] "mix5": 5 kiểu đều nhau (V2) | "hit_real": nghiêng về kiểu đoán sát đối thủ HIT thật
        # (SamSmartMath / chặn được là chặn: đoán đúng 57% nước đối thủ thật; ProCounter/ProShedder/Rule chỉ 45-46%)
        self.opp_pool_kind = opp_pool
        # [V3] search_all: MC xét TẤT CẢ nước hợp lệ (Sâm không so chất -> gộp nước cùng bộ số), kiểu vòng loại:
        # 8 mẫu cho mọi nước -> giữ nửa tốt -> +16 mẫu -> giữ 4 tốt nhất (+ nước heuristic) -> lấy mẫu như cũ.
        self.search_all = search_all
        # [V3.1] two_aggr: mức dùng heo chủ động (0 = như V3). Áp cho cả nước gốc lẫn chính sách mô phỏng của mình.
        self.two_aggr = two_aggr
        self.samples = samples
        self.max_samples = max_samples
        self.top_k = top_k
        self.override_z = override_z
        self.min_override_gain = min_override_gain
        self.opponent_mix = opponent_mix
        self.time_limit_sec = time_limit_sec
        self.min_samples = min_samples
        self.rng = random.Random(seed)
        self.policy = SamSmartMathBot(name + "_rollout", xin_sam_max_risk_pct)
        self.policy.two_aggr = two_aggr  # chính sách mô phỏng của mình dùng heo giống nước thật (nhất quán)
        self._pool: Optional[List[BaseSamBot]] = None
        self.last_mc_log: Dict[str, object] = {}

    @staticmethod
    def _mkey(m: SamCombo):
        return (m.is_pass, m.combo_type, tuple(sorted(card_rank(c) for c in m.cards)))

    human_lambda = 0.0   # [V4.7] cộng điểm theo thói quen NGƯỜI THẮNG (0 = tắt)
    pass_weight = True    # [V4.9.8/V4.9.30] chia bài ẩn theo lượt bỏ của đối thủ (người thật Sâm HIT/SUN có bộ rảnh là chặn)
    tester_mode = "v48"   # [V4.9.31] Mặc định bật bộ giải cuối ván + giữ bộ đỡ cho cả HIT và SUN

    def _significant(self, best: SamCombo, base: SamCombo, totals: Dict[SamCombo, List[int]]) -> Tuple[bool, float, float]:
        hp = getattr(self, "_hp", None) or {}
        bonus = self.human_lambda * (hp.get(best, 0.0) - hp.get(base, 0.0))
        diffs = [a - b + bonus for a, b in zip(totals[best], totals[base])]
        k = len(diffs)
        mean_d = sum(diffs) / k
        se = math.sqrt(sum((x - mean_d) ** 2 for x in diffs) / max(1, k - 1)) / math.sqrt(k)
        need = max(self.min_override_gain, self.override_z * se)
        need = min(need, SAM_MC_OVERRIDE_ABS)   # [V4.9.27] P6: hơn công thức gốc >= 1,5 lá là ghi đè (32 mẫu: ngưỡng cũ ~2,4 lá, 3 nước đợt 02/11 MC đúng mà bị giữ)
        return mean_d > need, mean_d, need

    # [V4.9.5] ĐỘ THÔNG MINH (Firebase): 100 = hết sức; núm chỉnh lấy từ `tlmn_bot_engine.intelligence_knobs`
    iq_level = 100
    iq_mc = True
    iq_endgame = True
    iq_blunder_rate = 0.0
    iq_blunder_width = 1
    last_iq_blunder = ""
    use_ai_api = True   # [V6.0 MASTER OFFLINE] Mặc định bật Hội đồng 3 Chuyên gia Offline V6 (Bellman-V6 + Pattern-Book + Lookahead-2Ply, 0đ API)

    def set_intelligence(self, knobs: Dict[str, object]) -> None:
        """Áp độ thông minh. Gọi SAU khi đã bật lối đánh theo profile (chỉ TẮT bớt tính năng, không bật thêm)."""
        if not hasattr(self, "_iq_base"):
            self._iq_base = {"samples": self.samples, "max_samples": self.max_samples, "min_samples": self.min_samples,
                             "time_limit_sec": self.time_limit_sec, "search_all": self.search_all}
        b = self._iq_base
        s = float(knobs.get("sample_scale", 1.0))
        self.iq_level = int(knobs.get("level", 100))
        if self.iq_level >= 100:
            self.samples, self.max_samples, self.min_samples = b["samples"], b["max_samples"], b["min_samples"]
            self.time_limit_sec = b["time_limit_sec"]
        else:
            self.samples = max(8, int(round(b["samples"] * s)))
            self.max_samples = None if b["max_samples"] is None else max(self.samples, int(round(b["max_samples"] * s)))
            self.min_samples = max(4, int(round(b["min_samples"] * s)))
            self.time_limit_sec = None if b["time_limit_sec"] is None else b["time_limit_sec"] * s
        self.search_all = bool(b["search_all"]) and bool(knobs.get("search_all", True))
        self.iq_mc = bool(knobs.get("mc", True))
        self.iq_blunder_rate = float(knobs.get("blunder_rate", 0.0))
        self.iq_blunder_width = int(knobs.get("blunder_width", 1))
        if not hasattr(self, "iq_rng"):
            self.iq_rng = random.Random()
        if not knobs.get("advanced", True):
            self.tester_mode = ""
            self.tester_rule = False
        if not knobs.get("fine", True):
            self.human_lambda = 0.0
            self.iq_endgame = False
            self.pass_weight = False
        else:
            self.iq_endgame = True

    def _iq_blunder(self, state: SamTableState, mv: SamCombo) -> SamCombo:
        """Độ thông minh < 100: thỉnh thoảng cố tình đi nước kém hơn (nước tốt nhì / top 3 / bất kỳ)."""
        self.last_iq_blunder = ""
        rate = self.iq_blunder_rate
        n = len(state.my_hand)
        if rate <= 0 or mv is None or state.xin_sam_player is not None or (not mv.is_pass and len(mv.cards) == n):
            return mv
        legal = get_legal_sam_moves(state.my_hand, state.board_combo, state.next_player_card_count)
        k_mv = self._mkey(mv)
        alts: Dict[tuple, SamCombo] = {}
        for m in legal:
            k = self._mkey(m)
            if k == k_mv or (not m.is_pass and len(m.cards) == n):
                continue
            alts.setdefault(k, m)
        if not alts or self.iq_rng.random() >= rate:
            return mv
        order: Dict[tuple, int] = {}
        for m in list(getattr(self, "last_rank", None) or []) + [m for _, m in (getattr(self, "last_candidates", None) or [])]:
            order.setdefault(self._mkey(m), len(order))
        pool = sorted(alts.items(), key=lambda kv: (order.get(kv[0], 10 ** 6), self.iq_rng.random()))
        w = self.iq_blunder_width
        pick = self.iq_rng.choice(pool[:w] if w > 0 else pool)[1]
        self.last_iq_blunder = f"{mv!r} -> {pick!r}"
        if isinstance(getattr(self, "last_mc_log", None), dict):
            self.last_mc_log["chosen"] = repr(pick)
        return pick

    def choose_move(self, state: SamTableState) -> SamCombo:
        self.last_iq_blunder = ""
        mv = self._choose_move_full(state)
        if self.iq_blunder_rate > 0:
            mv = self._iq_blunder(state, mv)
        return mv

    def _choose_move_full(self, state: SamTableState) -> SamCombo:
        self.last_rank = []
        return self._choose_move_mc(state)

    def _choose_move_mc(self, state: SamTableState) -> SamCombo:
        self.last_mc_log = {}
        self.policy.tester_rule = self.tester_rule
        self.policy.tester_mode = self.tester_mode
        self.policy.rule_set = self.rule_set
        _SAM_MC_RANK.rule_set = self.rule_set
        base_move = super().choose_move(state)
        if state.xin_sam_player is not None:
            return base_move
        if not self.iq_mc:
            return base_move

        legal = get_legal_sam_moves(state.my_hand, state.board_combo, state.next_player_card_count)
        non_pass_legal = [m for m in legal if not m.is_pass]
        for m in non_pass_legal:
            if len(m.cards) == len(state.my_hand) and not m.is_all_twos:
                self.last_mc_log = {
                    "base": repr(m),
                    "chosen": repr(m),
                    "override": "1 nhịp về đích ngay",
                    "scores": {repr(m): float(len(state.my_hand))},
                    "samples": 0,
                    "n_cands": 1,
                    "elapsed_sec": 0.0,
                }
                return m

        # Chỉ giữ luật cứng của Sâm Lốc: cấm để lại toàn 2 trên tay (trừ khi mọi nước đều để lại toàn 2) + Báo 1 giữ cửa
        safe_non_pass = [m for m in non_pass_legal if not would_leave_only_twos(state.my_hand, m)]
        if safe_non_pass:
            allowed_legal = list(safe_non_pass)
            if any(m.is_pass for m in legal) and state.board_combo is not None and state.min_opponent_cards > 1:
                allowed_legal.append(PASS_COMBO)
        else:
            allowed_legal = list(legal)
        if state.min_opponent_cards == 1:
            singles_sam = [m for m in allowed_legal if m.combo_type == SamComboType.SINGLE and not m.is_pass]
            multis_sam = [m for m in allowed_legal if not m.is_pass and m.length >= 2]
            if singles_sam:
                max_s_sam = max(m.order_value for m in singles_sam)
                if (state.board_combo is None or state.board_combo.is_pass) and multis_sam:
                    unseen_sam_mc = _sam_unseen(state)
                    boss_2step_sam = [
                        m for m in singles_sam
                        if is_boss_sam_combo(m, unseen_sam_mc)
                        and optimal_partition_sam_hand([c for c in state.my_hand if c not in m.cards]).num_turns == 1
                    ]
                    allowed_legal = multis_sam + boss_2step_sam
                else:
                    filtered_sam = [
                        m for m in allowed_legal
                        if not m.is_pass and (m.combo_type != SamComboType.SINGLE or m.order_value == max_s_sam)
                    ]
                    if filtered_sam:
                        allowed_legal = filtered_sam

        scored = list(getattr(self, "last_candidates", []) or [])
        sc_map: Dict[tuple, float] = {}
        best_move_by_key: Dict[tuple, SamCombo] = {}
        for sc, m in scored:
            k_m = self._mkey(m)
            if k_m not in sc_map or sc > sc_map[k_m]:
                sc_map[k_m] = sc
                best_move_by_key[k_m] = m

        seen_cands: Dict[tuple, SamCombo] = {}
        for m in allowed_legal:
            k_m = self._mkey(m)
            seen_cands.setdefault(k_m, best_move_by_key.get(k_m, m))

        # Bổ sung điểm từ mạng nơ-ron DouZero-Solo-SAM (chỉ tính 1 lần trên mỗi _mkey đã gộp)
        try:
            from ai_tactician_api import eval_sam_candidate
            for k_m, m in seen_cands.items():
                nn_sc = eval_sam_candidate(state, m)
                sc_map[k_m] = sc_map.get(k_m, 0.0) + nn_sc * 3.0
        except Exception:
            pass

        all_ranked = sorted(seen_cands.values(), key=lambda m: -sc_map.get(self._mkey(m), -999.0))

        best_prior_sc = max((sc_map.get(self._mkey(m), -999.0) for m in all_ranked), default=0.0)
        soft_filtered = [
            m for m in all_ranked
            if sc_map.get(self._mkey(m), -999.0) >= best_prior_sc - 95.0
        ]
        cands = list(soft_filtered[:max(self.top_k, 6)])
        if base_move not in cands and base_move in all_ranked:
            cands.insert(0, base_move)
        # Luôn giữ ít nhất 4 ứng viên tốt nhất khi có >= 2 nước đi hợp lệ để IS-MCTS luôn chạy mô phỏng đầy đủ
        target_min_sam = min(len(all_ranked), 4)
        if len(cands) < target_min_sam:
            for m in all_ranked:
                if m not in cands:
                    cands.append(m)
                if len(cands) >= target_min_sam:
                    break

        if len(cands) <= 1:
            chosen_only = cands[0] if cands else base_move
            self.last_mc_log = {
                "base": repr(chosen_only),
                "chosen": repr(chosen_only),
                "override": "1 nước hợp lệ duy nhất",
                "scores": {repr(chosen_only): 0.0},
                "samples": 0,
                "n_cands": len(cands),
                "elapsed_sec": 0.0,
            }
            return chosen_only

        n = state.num_players
        me = state.my_seat
        known = set(state.my_hand) | set(state.played_cards)
        unseen = [c for c in range(52) if c not in known]
        opp_seats = [s for s in range(n) if s != me and state.cards_left[s] > 0]
        if sum(state.cards_left[s] for s in opp_seats) > len(unseen):
            return base_move
        if self.opponent_mix and self._pool is None:
            if self.opp_pool_kind == "hit_real":
                self._pool = [SamSmartMathBot("m1"), SamSmartMathBot("m1b"), SamNeverPassBot("m6", cheapest=False),
                              SamProCounterBot("m2"), SamProShedderBot("m3")]
            else:
                self._pool = [SamSmartMathBot("m1"), SamSmartMathBot("m1b"), SamProCounterBot("m2"),
                              SamProShedderBot("m3"), SamRuleBot("m4")]
        totals: Dict[SamCombo, List[float]] = {m: [] for m in cands}
        thoi_counts: Dict[SamCombo, int] = {m: 0 for m in cands}
        pass_log = getattr(state, "opp_pass_log", None) or {}
        use_pw = bool(self.pass_weight and any(pass_log.get(s) for s in opp_seats))
        self._hp = sam_human_prior_scores(state, list(cands)) if self.human_lambda > 0 else {}
        hp = self._hp
        active: List[SamCombo] = list(cands)
        t0 = time.monotonic()
        _ai_futures = []
        _ai_top_sam: Optional[SamCombo] = None
        if getattr(self, "use_ai_api", False) and len(cands) >= 2:
            try:
                from ai_tactician_api import build_sam_tactical_prompt, launch_ai_council_async
                _sam_prompt = build_sam_tactical_prompt(state, cands, getattr(self, "recent_moves", None))
                _ai_futures = launch_ai_council_async(_sam_prompt, len(cands))
                if _ai_futures:
                    _res0 = _ai_futures[0][2].result(timeout=0.05)
                    if _res0 and _res0[1] is not None and 0 <= _res0[1] < len(cands):
                        _ai_top_sam = cands[_res0[1]]
            except Exception:
                _ai_futures = []
        def _sam_prior_reg(m: SamCombo) -> float:
            u_m = sc_map.get(self._mkey(m), best_prior_sc - 20.0)
            return max(-1.10, min(0.0, 0.025 * (u_m - best_prior_sc)))

        cap = max(self.samples, self.max_samples or 0)
        for k in range(cap):
            if (self.time_limit_sec is not None and k >= (8 if self.search_all else self.min_samples)
                    and time.monotonic() - t0 > self.time_limit_sec):
                break
            if self.search_all and k in (8, 24) and len(active) > 4:
                keep = 4 if k == 24 else max(4, (len(active) + 1) // 2)
                ranked = sorted(active, key=lambda m: -(sum(totals[m]) / len(totals[m]) + _sam_prior_reg(m)))
                new_active = ranked[:keep]
                if base_move in active and base_move not in new_active:
                    new_active.append(base_move)
                if _ai_top_sam is not None and _ai_top_sam in active and _ai_top_sam not in new_active:
                    new_active.append(_ai_top_sam)
                active = new_active
            if k >= self.samples and (k - self.samples) % 8 == 0 and len(active) >= 2:
                ranked_now = sorted(active, key=lambda m: -(sum(totals[m]) / len(totals[m]) + _sam_prior_reg(m)))
                if self._significant(ranked_now[0], ranked_now[1], totals)[0]:
                    break
            hands: List[List[int]] = [[] for _ in range(n)]
            hands[me] = list(state.my_hand)
            best_w = -1.0
            best_h: Optional[List[List[int]]] = None
            for _try in range(48 if use_pw else 1):
                self.rng.shuffle(unseen)
                pos = 0
                w = 1.0
                for s in opp_seats:
                    hands[s] = unseen[pos: pos + state.cards_left[s]]
                    pos += state.cards_left[s]
                    if use_pw:
                        for bd, after in pass_log.get(s, []):
                            w *= sam_pass_likelihood(list(hands[s]) + list(after), bd)
                if not use_pw or self.rng.random() < w:
                    best_h = None
                    break
                if w > best_w:
                    best_w, best_h = w, [list(x) for x in hands]
            if best_h is not None:
                hands = best_h
            pols: List[BaseSamBot] = [self.policy] * n
            if self.opponent_mix:
                pols = [self.policy if s == me else self.rng.choice(self._pool) for s in range(n)]
            init_counts = [10 if state.cards_left[s] == 10 else 99 for s in range(n)]
            init_counts[me] = 10 if len(state.my_hand) == 10 else 99
            for m in active:
                h = [list(x) for x in hands]
                played = list(state.played_cards)
                passed = list(state.passed_in_round)
                board, owner = state.board_combo, state.board_owner
                ce: Optional[Tuple[int, int, int]] = None
                if m.is_pass:
                    passed[me] = True
                else:
                    for c in m.cards:
                        h[me].remove(c)
                        played.append(c)
                    if (board is not None and board.combo_type == SamComboType.SINGLE and board.order_value == RANK_2
                            and m.combo_type == SamComboType.FOUR_OF_KIND and owner is not None):
                        ce = (me, owner, ACTIVE_SAM_RULE.chop_two)
                    board, owner = m, me
                    if not h[me]:
                        d = [0] * n
                        if ce is not None:
                            d[me] += ce[2]
                        if m.is_all_twos:
                            d[me] = -ACTIVE_SAM_RULE.finish_two_penalty * (n - 1)
                        else:
                            for s in range(n):
                                if s == me:
                                    continue
                                rem = h[s]
                                twos = sum(1 for c in rem if card_rank(c) == RANK_2)
                                quads = sum(1 for _, q in Counter(card_rank(c) for c in rem).items() if q == 4)
                                base = ACTIVE_SAM_RULE.cong if init_counts[s] == len(rem) else len(rem)
                                d[me] += base + twos * ACTIVE_SAM_RULE.thoi_two + quads * ACTIVE_SAM_RULE.thoi_four
                        totals[m].append(d[me])
                        continue
                nxt = (me + 1) % n
                d = rollout_sam_from_state(h, played, board, owner, passed, nxt, pols, init_counts, chop_event=ce)
                val_me = float(d[me])
                if val_me < 0 and h[me]:
                    _my_twos_left = sum(1 for c in h[me] if card_rank(c) == RANK_2)
                    if _my_twos_left > 0:
                        thoi_counts[m] += 1
                        val_me -= 0.65 * float(_my_twos_left * ACTIVE_SAM_RULE.thoi_two)
                totals[m].append(val_me)

        def _sam_prior_reg(m: SamCombo) -> float:
            u_m = sc_map.get(self._mkey(m), best_prior_sc - 20.0)
            return max(-1.10, min(0.0, 0.025 * (u_m - best_prior_sc)))

        mean = lambda m: sum(totals[m]) / len(totals[m]) + self.human_lambda * hp.get(m, 0.0) + _sam_prior_reg(m)
        best = max(active, key=mean)
        note = f"IS-MCTS chọn (EV={mean(best):+.2f} lá)"
        _ai_summary = ""
        if _ai_futures:
            try:
                from ai_tactician_api import collect_ai_council_votes, combine_ai_and_mc_decision
                _ai_votes, _ai_details = collect_ai_council_votes(_ai_futures, t0 + 3.6)
                if _ai_votes:
                    _mc_sc_map = {
                        m: mean(m)
                        for m in active
                        if totals.get(m)
                    }
                    _n_smp = max((len(v) for v in totals.values()), default=0)
                    best, _ai_summary = combine_ai_and_mc_decision(
                        cands, best, _mc_sc_map, _ai_votes, _ai_details, self._mkey,
                        thoi_counts=thoi_counts, num_samples=_n_smp
                    )
                    note = f"{note} | {_ai_summary}".strip(" |")
            except Exception as _e_ai:
                _ai_summary = f"ai_err:{_e_ai}"
        self.last_rank = [best] + sorted((m for m in active if m != best), key=mean, reverse=True) + sorted(
            (m for m in totals if m not in active and totals[m]), key=mean, reverse=True)
        self.last_mc_log = {
            "base": repr(base_move), "chosen": repr(best), "override": note,
            "ai_council": _ai_summary,
            "scores": {repr(m): round(mean(m), 2) for m, v in totals.items() if v and m in active},
            "samples": max(len(v) for v in totals.values()), "n_cands": len(cands), "elapsed_sec": round(time.monotonic() - t0, 3),
        }
        return best

# ============================================================================
# 7. HỆ THỐNG KIỂM ĐỊNH ĐA DẠNG (DUPLICATE BENCHMARK + XIN SÂM CALIBRATION)
# ============================================================================

def run_duplicate_sam_benchmark(
    bot_factories: List[Tuple[str, callable]],
    num_deals: int = 250,
    seed: int = 2026,
) -> Dict[str, Dict[str, float]]:
    """
    Chạy giải đấu Duplicate Sâm Lốc:
    Với mỗi bộ bài chia ngẫu nhiên, xoay vòng vị trí ngồi (Rotation) để mọi Bot đều được cầm
    chính xác các bộ bài giống hệt nhau, triệt tiêu 100% yếu tố may mắn bài đẹp/xấu!
    """
    num_players = len(bot_factories)
    rng = random.Random(seed)
    stats = {
        name: {
            "total_cards": 0,
            "wins": 0,
            "hands": 0,
            "xin_sam_attempts": 0,
            "xin_sam_wins": 0,
        }
        for name, _ in bot_factories
    }

    deck = list(range(52))
    for deal_idx in range(num_deals):
        rng.shuffle(deck)
        base_hands = [sorted(deck[i * 10 : (i + 1) * 10]) for i in range(num_players)]

        # Xoay vòng vị trí ngồi `shift` từ 0 đến num_players - 1
        for shift in range(num_players):
            rotated_factories = bot_factories[shift:] + bot_factories[:shift]
            bots = [factory() for _, factory in rotated_factories]
            names = [name for name, _ in rotated_factories]

            res = simulate_sam_hand(bots, base_hands, starting_seat=0, allow_xin_sam=True)
            for s, name in enumerate(names):
                stats[name]["total_cards"] += res.card_deltas[s]
                stats[name]["hands"] += 1
                if res.winner_seat == s:
                    stats[name]["wins"] += 1
                if res.xin_sam_seat == s:
                    stats[name]["xin_sam_attempts"] += 1
                    if res.xin_sam_success:
                        stats[name]["xin_sam_wins"] += 1

    return stats


def run_xin_sam_risk_calibration_test(
    risk_thresholds: Sequence[float] = (0.0, 5.0, 10.0, 15.0, 20.0, 30.0, 50.0),
    num_players: int = 4,
    num_test_hands: int = 2000,
    seed: int = 9999,
) -> None:
    """
    Kiểm định chuyên sâu tính năng XIN SÂM (Báo Sâm) theo tham số `% mạo hiểm` (`max_risk_percent`):
    - Tạo tập bài thử nghiệm gồm cả các thế bài Sâm tiềm năng (Sảnh dài, nhiều 2, Sám/Đôi lớn)
      và bài ngẫu nhiên.
    - Đo lường với từng mức `max_risk_percent` (0%, 5%, 10%, 15%, 20%, 30%, 50%):
      + Tần suất quyết định Xin Sâm.
      + Tỷ lệ Ăn Sâm thành công thực tế (Actual Success Rate %).
      + Tỷ lệ Bị bắt đền Sâm thực tế (Actual Caught Risk % - so sánh với `max_risk_percent`).
      + Tổng lợi nhuận ròng (Net Cards Won/Lost từ Xin Sâm).
    """
    print("\n" + "=" * 88)
    print(f"BẢNG KIỂM ĐỊNH TOÁN HỌC 'XIN SÂM' THEO % MẠO HIỂM ({num_players} NGƯỜI CHƠI - {num_test_hands} VÁN)")
    print("=" * 88)
    print(
        f"{'Mức Mạo Hiểm Input':<20} | {'Số Lần Xin Sâm':<15} | {'Ăn Sâm Thành Công':<18} | "
        f"{'Rủi Ro Thực Tế':<15} | {'Lợi Nhuận Ròng (Lá)':<18}"
    )
    print("-" * 88)

    rng = random.Random(seed)
    deck = list(range(52))

    # Tạo bộ dữ liệu hỗn hợp: 50% ván chia hoàn toàn ngẫu nhiên + 50% ván bài đẹp ứng viên Báo Sâm
    deals: List[List[List[int]]] = []
    for i in range(num_test_hands):
        if i % 2 == 0:
            rng.shuffle(deck)
            deals.append([sorted(deck[p * 10 : (p + 1) * 10]) for p in range(num_players)])
        else:
            # Sinh ván bài mà Seat 0 có cấu trúc bài mạnh (có sảnh hoặc bài cao) để test ranh giới Xin Sâm
            best_h0 = None
            best_sc = -1e9
            for _ in range(6):
                rng.shuffle(deck)
                cand_h0 = sorted(deck[:10])
                plan = optimal_partition_sam_hand(cand_h0)
                if plan.total_score > best_sc:
                    best_sc = plan.total_score
                    best_h0 = list(deck)
            assert best_h0 is not None
            deals.append([sorted(best_h0[p * 10 : (p + 1) * 10]) for p in range(num_players)])

    for max_risk in risk_thresholds:
        attempts = 0
        successes = 0
        net_cards = 0

        for hands in deals:
            analysis = evaluate_xin_sam(
                hand=hands[0],
                num_players=num_players,
                max_risk_percent=max_risk,
                num_simulations=150,
                rng=rng,
            )
            if analysis.should_declare:
                attempts += 1
                bots = [
                    SamSmartMathBot("Tester", xin_sam_max_risk_pct=max_risk),
                    SamProCounterBot("Opp1", xin_sam_max_risk_pct=-1.0),
                    SamProShedderBot("Opp2", xin_sam_max_risk_pct=-1.0),
                    SamRuleBot("Opp3", xin_sam_max_risk_pct=-1.0),
                ][:num_players]
                res = simulate_sam_hand(bots, hands, starting_seat=0, allow_xin_sam=True)
                if res.xin_sam_seat == 0:
                    if res.xin_sam_success:
                        successes += 1
                    net_cards += res.card_deltas[0]

        if attempts > 0:
            win_rate = (successes / attempts) * 100.0
            actual_risk = 100.0 - win_rate
            print(
                f"{f'<= {max_risk:5.1f}%':<20} | {f'{attempts}/{num_test_hands}':<15} | "
                f"{f'{successes} ({win_rate:5.1f}%)':<18} | {f'{actual_risk:6.2f}%':<15} | "
                f"{net_cards:+15d} lá"
            )
        else:
            print(
                f"{f'<= {max_risk:5.1f}%':<20} | {'0':<15} | {'0 (100.0%)':<18} | {'0.00%':<15} | {'+0 lá':<18}"
            )
    print("=" * 88)


def showcase_specific_sam_scenarios() -> None:
    """Trình diễn các tình huống đặc thù của Sâm Lốc SUN: Sảnh A-2-3, 2-3-4, Cấm về 2, Báo 1 và Xin Sâm."""
    print("\n" + "=" * 88)
    print("KIỂM TRA CÁC TÌNH HUỐNG ĐẶC THÙ LUẬT SÂM LỐC SUN.WIN")
    print("=" * 88)

    # Tình huống 1: So sánh thứ tự Sảnh A-2-3 < 2-3-4 < 3-4-5 < ... < Q-K-A
    h_straights = [
        parse_card("A♠"), parse_card("2♥"), parse_card("3♦"),
        parse_card("4♣"), parse_card("5♠"),
        parse_card("Q♦"), parse_card("K♣"),
    ]
    combos = [c for c in generate_all_sam_combos(h_straights) if c.combo_type == SamComboType.STRAIGHT and c.length == 3]
    combos.sort(key=lambda c: c.order_value)
    print("1. Thứ tự Sảnh 3 lá trong Sâm Lốc:")
    print("   " + " < ".join(f"{c.label} (order={c.order_value})" for c in combos))

    # Tình huống 2: Kiểm tra chống Về nhất bằng 2 (2-Combo Endgame Theorem)
    hand_endgame = [parse_card("2♠"), parse_card("2♥"), parse_card("7♦"), parse_card("7♣")]
    bot = SamSmartMathBot("SamSmartMathBot", xin_sam_max_risk_pct=10.0)
    state_end = SamTableState(
        num_players=4,
        my_seat=0,
        my_hand=hand_endgame,
        board_combo=None,
        board_owner=None,
        cards_left=[4, 5, 6, 4],
        played_cards=[],
        passed_in_round=[False] * 4,
    )
    chosen_end = bot.choose_move(state_end)
    print(f"\n2. Tình huống cầm [Đôi 2 + Đôi 7] khi mở vòng cuối:")
    print(f"   - Bài trên tay: {hand_str(hand_endgame)}")
    print(f"   - Bot chọn đánh trước: {chosen_end} (Tuyệt đối KHÔNG đánh Đôi 7 trước để tránh bị Thối Đôi 2!)")

    # Tình huống 3: Kiểm tra Giữ Cửa khi nhà kế tiếp Báo 1
    hand_gate = [parse_card("4♠"), parse_card("9♦"), parse_card("A♥")]
    state_gate = SamTableState(
        num_players=4,
        my_seat=0,
        my_hand=hand_gate,
        board_combo=SamCombo(SamComboType.SINGLE, (parse_card("6♣"),), 1, RANK_6, "Lẻ 6"),
        board_owner=2,
        cards_left=[3, 1, 4, 5],  # Seat 1 (nhà kế tiếp) còn đúng 1 lá (Báo 1)!
        played_cards=[],
        passed_in_round=[False] * 4,
    )
    chosen_gate = bot.choose_move(state_gate)
    print(f"\n3. Tình huống Giữ Cửa khi nhà dưới Báo 1 (trên bàn là Lẻ 6, trên tay có 4♠, 9♦, A♥):")
    print(f"   - Bot bắt buộc đánh: {chosen_gate} (Đúng luật Giữ Cửa bằng cây lẻ lớn nhất A♥, tránh đền 15 lá!)")

    # Tình huống 4: Phân tích Xin Sâm với các mức % mạo hiểm khác nhau trên cùng 1 bộ bài
    hand_sam = [
        parse_card("10♠"), parse_card("J♦"), parse_card("Q♣"), parse_card("K♥"), parse_card("A♠"),
        parse_card("2♦"), parse_card("2♣"),
        parse_card("A♦"), parse_card("A♥"),
        parse_card("8♥"),
    ]
    print(f"\n4. Phân tích Xin Sâm trên bộ bài: {hand_str(hand_sam)} (Sảnh 10-J-Q-K-A + Đôi 2 + Đôi A + Lẻ 8):")
    for risk_in in (1.0, 10.0, 18.0, 25.0):
        ans = evaluate_xin_sam(hand_sam, num_players=4, max_risk_percent=risk_in, num_simulations=300)
        print(f"   * Input mạo hiểm tối đa = {risk_in:4.1f}% -> {ans.reason}")

    # Tình huống 5: Kiểm tra Regression thực chiến từ ván Solo Room 28839 (Cầm 3♣ + Sảnh 8-Q + A♥ + 2♠)
    # Không được nhốt A♥ và 2♠ vào Sảnh A-2-3 khi còn nhiều bài, không được bỏ lượt trước Lẻ K,
    # và không được xé Sảnh 8-Q ra đánh Q♥ khi có sẵn A♥ / 2♠!
    hand_r28839 = [
        parse_card("3♣"), parse_card("8♦"), parse_card("9♠"), parse_card("10♣"),
        parse_card("J♣"), parse_card("Q♥"), parse_card("A♥"), parse_card("2♠"),
    ]
    plan_r28839 = optimal_partition_sam_hand(hand_r28839)
    combo_labels = [c.label for c in plan_r28839.combos]
    assert "Sảnh A-2-3" not in combo_labels, f"LỖI: Không được gom A-2-3 khi còn 8 lá! ({combo_labels})"

    # Khi đối thủ (còn 4 lá) đánh Lẻ K(K♦): Bot bắt buộc phải đánh 2♠ (hoặc A♥), tuyệt đối không PASS!
    state_r28839_k = SamTableState(
        num_players=2,
        my_seat=0,
        my_hand=hand_r28839,
        board_combo=SamCombo(SamComboType.SINGLE, (parse_card("K♦"),), 1, RANK_K, "Lẻ K"),
        board_owner=1,
        cards_left=[8, 4],
        played_cards=[
            parse_card("7♠"), parse_card("7♣"), parse_card("7♦"),
            parse_card("3♦"), parse_card("5♠"), parse_card("10♠"), parse_card("J♥"), parse_card("K♦"),
        ],
        passed_in_round=[False, False],
    )
    mv_on_k = bot.choose_move(state_r28839_k)
    assert not mv_on_k.is_pass and mv_on_k.order_value in (RANK_A, RANK_2), (
        f"LỖI: Phải đánh A hoặc 2 đè Lẻ K, nhưng bot lại chọn {mv_on_k}!"
    )

    # Khi đối thủ (còn 3 lá) đánh Lẻ 5(5♥): Bot tuyệt đối không được xé Q♥ khỏi Sảnh 8-Q mà phải đánh 2♠ / A♥!
    state_r28839_5 = SamTableState(
        num_players=2,
        my_seat=0,
        my_hand=hand_r28839,
        board_combo=SamCombo(SamComboType.SINGLE, (parse_card("5♥"),), 1, RANK_5, "Lẻ 5"),
        board_owner=1,
        cards_left=[8, 3],
        played_cards=[
            parse_card("7♠"), parse_card("7♣"), parse_card("7♦"),
            parse_card("3♦"), parse_card("5♠"), parse_card("10♠"), parse_card("J♥"), parse_card("K♦"), parse_card("5♥"),
        ],
        passed_in_round=[False, False],
    )
    mv_on_5 = bot.choose_move(state_r28839_5)
    assert not mv_on_5.is_pass and mv_on_5.order_value in (RANK_A, RANK_2), (
        f"LỖI: Không được xé Sảnh 8-Q đánh {mv_on_5}, phải đánh 2♠ hoặc A♥!"
    )

    # Sau khi đánh 2♠ cướp cái, đến lượt mình mở vòng với [3♣, Sảnh 8-Q, A♥]: Phải xả Sảnh 8-Q ngay!
    hand_after_2 = [c for c in hand_r28839 if c != parse_card("2♠")]
    state_lead_after_2 = SamTableState(
        num_players=2,
        my_seat=0,
        my_hand=hand_after_2,
        board_combo=None,
        board_owner=None,
        cards_left=[7, 4],
        played_cards=state_r28839_k.played_cards + [parse_card("2♠")],
        passed_in_round=[False, False],
    )
    mv_lead_sanh = bot.choose_move(state_lead_after_2)
    assert mv_lead_sanh.combo_type == SamComboType.STRAIGHT and mv_lead_sanh.length == 5, (
        f"LỖI: Sau khi cướp cái bằng 2♠ phải xả Sảnh 8-Q (5 lá), nhưng bot chọn {mv_lead_sanh}!"
    )

    # Sau khi xả Sảnh 8-Q, trên tay còn 2 lá [3♣, A♥]: Khi mở vòng phải đánh A♥ trước rồi hạ 3♣!
    hand_last_2 = [parse_card("3♣"), parse_card("A♥")]
    state_lead_last_2 = SamTableState(
        num_players=2,
        my_seat=0,
        my_hand=hand_last_2,
        board_combo=None,
        board_owner=None,
        cards_left=[2, 4],
        played_cards=state_lead_after_2.played_cards + list(mv_lead_sanh.cards),
        passed_in_round=[False, False],
    )
    mv_lead_ace = bot.choose_move(state_lead_last_2)
    assert mv_lead_ace.order_value == RANK_A, f"LỖI: Còn [3♣, A♥] phải đánh A♥ trước, nhưng bot chọn {mv_lead_ace}!"

    print("\n5. Kiểm tra Regression Thực Chiến Ván Solo Room 28839 (Cầm 3♣ + Sảnh 8-Q + A♥ + 2♠):")
    print(f"   - Phân rã DP mới     : {[str(c) for c in plan_r28839.combos]} (Giữ A♥ và 2♠ độc lập để bắt cái!)")
    print(f"   - Đối thủ đánh Lẻ K  : Bot đánh ngay {mv_on_k} (Cướp cái 100%, chống Thối 2!)")
    print(f"   - Đối thủ đánh Lẻ 5  : Bot đánh ngay {mv_on_5} (Tuyệt đối không xé Q♥ khỏi Sảnh 8-Q!)")
    print(f"   - Nhịp mở vòng kế    : Bot xả ngay {mv_lead_sanh} (Thoát 5 lá cùng lúc!)")
    print(f"   - Còn [3♣, A♥] cuối  : Bot đánh {mv_lead_ace} trước -> hạ 3♣ về đích chuẩn xác!")

    # Tình huống 6: Kiểm tra 5 Mẹo Cao Thủ Sâm Lốc Chống Bẫy từ Phân Tích Log Tự Động
    # 6a. Không tự ý mở vòng bằng Sảnh A-2-3 khi trên tay còn bài khác
    hand_trap_a23 = [
        parse_card("A♦"), parse_card("2♣"), parse_card("3♠"),
        parse_card("7♣"), parse_card("7♥"), parse_card("10♦"),
    ]
    state_trap_a23 = SamTableState(
        num_players=2, my_seat=0, my_hand=hand_trap_a23,
        board_combo=None, board_owner=None, cards_left=[6, 6],
        played_cards=[], passed_in_round=[False, False],
    )
    mv_trap_a23 = bot.choose_move(state_trap_a23)
    assert not (mv_trap_a23.combo_type == SamComboType.STRAIGHT and mv_trap_a23.order_value == 0), (
        f"LỖI: Không được đánh Sảnh A-2-3 khi còn bài khác! ({mv_trap_a23})"
    )

    # 6b. Mở vòng khi cầm nhiều Đôi (Đôi 3 + Đôi A + Sảnh) ở đầu ván: phải đánh Đôi 3 dò đường trước, giữ Đôi A!
    hand_trap_pairs = [
        parse_card("3♦"), parse_card("3♥"),
        parse_card("A♣"), parse_card("A♥"),
        parse_card("6♠"), parse_card("7♦"), parse_card("8♣"),
        parse_card("K♠"),
    ]
    state_trap_pairs = SamTableState(
        num_players=2, my_seat=0, my_hand=hand_trap_pairs,
        board_combo=None, board_owner=None, cards_left=[8, 8],
        played_cards=[], passed_in_round=[False, False],
    )
    mv_trap_pairs = bot.choose_move(state_trap_pairs)
    assert not (mv_trap_pairs.combo_type == SamComboType.PAIR and mv_trap_pairs.order_value == RANK_A), (
        f"LỖI: Đầu ván cầm Đôi 3 + Đôi A không được đánh Đôi A trước! ({mv_trap_pairs})"
    )

    # 6c. Đỡ bài lẻ khi có sẵn lá đơn rời <= K (vd có K♠ rời + A♥ + 2♦ khi bàn đánh Lẻ 10): đánh K♠ trước, giữ A/2!
    hand_trap_ladder = [
        parse_card("4♣"), parse_card("5♦"), parse_card("6♥"),
        parse_card("9♣"), parse_card("9♠"),
        parse_card("K♠"), parse_card("A♥"), parse_card("2♦"),
    ]
    state_trap_ladder = SamTableState(
        num_players=2, my_seat=0, my_hand=hand_trap_ladder,
        board_combo=SamCombo(SamComboType.SINGLE, (parse_card("10♣"),), 1, RANK_10, "Lẻ 10"),
        board_owner=1, cards_left=[8, 7],
        played_cards=[parse_card("10♣")], passed_in_round=[False, False],
    )
    mv_trap_ladder = bot.choose_move(state_trap_ladder)
    assert mv_trap_ladder.combo_type == SamComboType.SINGLE and mv_trap_ladder.order_value == RANK_K, (
        f"LỖI: Có Lẻ K đứng rời phải đánh Lẻ K đỡ Lẻ 10 trước khi dùng A/2! ({mv_trap_ladder})"
    )

    # 6d. Cắt sảnh dài 7 lá (5-6-7-8-9-10-J) để đỡ Sảnh 3-5 trên bàn: phải cắt đầu cao Sảnh 9-J để giữ cái!
    hand_trap_straight = [
        parse_card("5♠"), parse_card("6♦"), parse_card("7♣"),
        parse_card("8♥"), parse_card("9♠"), parse_card("10♦"), parse_card("J♣"),
    ]
    state_trap_straight = SamTableState(
        num_players=2, my_seat=0, my_hand=hand_trap_straight,
        board_combo=SamCombo(
            SamComboType.STRAIGHT,
            (parse_card("3♣"), parse_card("4♦"), parse_card("5♥")),
            3, 2, "Sảnh 3-5",
        ),
        board_owner=1, cards_left=[7, 6],
        played_cards=[parse_card("3♣"), parse_card("4♦"), parse_card("5♥")],
        passed_in_round=[False, False],
    )
    mv_trap_straight = bot.choose_move(state_trap_straight)
    assert mv_trap_straight.combo_type == SamComboType.STRAIGHT and mv_trap_straight.order_value >= 7, (
        f"LỖI: Khi cắt sảnh dài đỡ Sảnh 3-5 phải cắt đầu cao (Sảnh 9-J), nhưng chọn {mv_trap_straight}!"
    )

    # 6e. Mở vòng khi bài KHÔNG có 2 (vd: 3, 5-6-7, 9-10-J, A): tỉ lệ đối thủ cầm 2 cao,
    # bắt buộc phải chạy lá (đánh Sảnh 9-10-J -> Sảnh 5-6-7) trước, tuyệt đối không đánh Lẻ 3 trước!
    hand_run_no_two = [
        parse_card("3♠"),
        parse_card("5♠"), parse_card("6♦"), parse_card("7♣"),
        parse_card("9♥"), parse_card("10♠"), parse_card("J♦"),
        parse_card("A♥"),
    ]
    state_run_no_two = SamTableState(
        num_players=2, my_seat=0, my_hand=hand_run_no_two,
        board_combo=None, board_owner=None, cards_left=[8, 8],
        played_cards=[], passed_in_round=[False, False],
    )
    mv_run_no_two = bot.choose_move(state_run_no_two)
    assert mv_run_no_two.combo_type == SamComboType.STRAIGHT, (
        f"LỖI: Bài [3, 5-6-7, 9-10-J, A] phải chạy Sảnh trước, không được đánh {mv_run_no_two}!"
    )

    # 6f. Mở vòng khi bài CÓ 2 + Sảnh + Lẻ 3 (vd: [3, 5-6-7-8-9-10-J, 2] và [3, 5-6-7, 9-10-J, 2]):
    # Tuyệt đối không đánh Lẻ 3 trước (bị đối thủ chặn 2 sẽ tịt thối 2), phải đánh bộ Sảnh có khả năng
    # không ai chặn được cao nhất trước, sau đó đập 2 rồi về 3 đốt cháy bài đối thủ!
    hand_run_with_two_long = [
        parse_card("3♠"),
        parse_card("5♠"), parse_card("6♦"), parse_card("7♣"),
        parse_card("8♥"), parse_card("9♠"), parse_card("10♦"), parse_card("J♣"),
        parse_card("2♥"),
    ]
    state_run_with_two_long = SamTableState(
        num_players=2, my_seat=0, my_hand=hand_run_with_two_long,
        board_combo=None, board_owner=None, cards_left=[9, 9],
        played_cards=[], passed_in_round=[False, False],
    )
    mv_run_with_two_long = bot.choose_move(state_run_with_two_long)
    assert mv_run_with_two_long.combo_type == SamComboType.STRAIGHT and mv_run_with_two_long.length == 7, (
        f"LỖI: Bài [3, 5-6-7-8-9-10-J, 2] phải đánh Sảnh 5-J trước, không được đánh {mv_run_with_two_long}!"
    )

    hand_run_with_two_split = [
        parse_card("3♠"),
        parse_card("5♠"), parse_card("6♦"), parse_card("7♣"),
        parse_card("9♠"), parse_card("10♦"), parse_card("J♣"),
        parse_card("2♥"),
    ]
    state_run_with_two_split = SamTableState(
        num_players=2, my_seat=0, my_hand=hand_run_with_two_split,
        board_combo=None, board_owner=None, cards_left=[8, 8],
        played_cards=[], passed_in_round=[False, False],
    )
    mv_run_with_two_split = bot.choose_move(state_run_with_two_split)
    assert mv_run_with_two_split.combo_type == SamComboType.STRAIGHT and mv_run_with_two_split.label == "Sảnh 9-J", (
        f"LỖI: Bài [3, 5-6-7, 9-10-J, 2] phải đánh Sảnh 9-J trước, không được đánh {mv_run_with_two_split}!"
    )

    print("\n6. Kiểm tra Bộ Mẹo Chơi Sâm Cao Thủ Chống Bẫy (Log Audit):")
    print(f"   - Chống bẫy mở Sảnh A-2-3 sớm : Bot chọn {mv_trap_a23} (Giữ A♦ và 2♣!)")
    print(f"   - Cầm [Đôi 3 + Đôi A + Sảnh]  : Bot mở vòng bằng {mv_trap_pairs} (Giữ Đôi A thu hồi cái!)")
    print(f"   - Đỡ Lẻ 10 khi có [K♠, A♥, 2♦]: Bot đánh {mv_trap_ladder} trước (Giữ A♥ và 2♦ cho lượt sau!)")
    print(f"   - Cắt sảnh 5..J đỡ Sảnh 3-5   : Bot cắt đầu cao {mv_trap_straight} (Giữ cái để đánh nốt 5-6-7-8!)")
    print(f"   - Bài [3, 5-6-7, 9-10-J, A]   : Bot chạy lá {mv_run_no_two} trước (Chống đối thủ cầm 2 bắt A!)")
    print(f"   - Bài [3, 5-6-7-8-9-10-J, 2]  : Bot đánh {mv_run_with_two_long} -> đập 2 -> về 3 (Đốt cháy đối thủ!)")
    print(f"   - Bài [3, 5-6-7, 9-10-J, 2]   : Bot đánh {mv_run_with_two_split} -> 5-6-7 -> 2 -> 3 (Chống Thối 2!)")
    print("   => TẤT CẢ ASSERTIONS CHIẾN THUẬT ĐỀU PASS 100%!")


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.time()
    showcase_specific_sam_scenarios()

    # Kiểm định độ chính xác của tham số % mạo hiểm Xin Sâm
    run_xin_sam_risk_calibration_test(
        risk_thresholds=(0.0, 5.0, 10.0, 15.0, 20.0, 30.0, 50.0),
        num_players=4,
        num_test_hands=1200,
    )

    # Chạy giải đấu Duplicate trên cả 4 quy mô bàn chơi: 5 người, 4 người, 3 người, 2 người (Solo)
    table_configs = [
        (
            "BÀN 5 NGƯỜI (5-PLAYER TABLE)",
            [
                ("SamSmartMathBot (AI Toán Học)", lambda: SamSmartMathBot("SamSmartMathBot", xin_sam_max_risk_pct=12.0)),
                ("SamProCounterBot (Đếm Bài)", lambda: SamProCounterBot("SamProCounterBot", xin_sam_max_risk_pct=8.0)),
                ("SamProShedderBot (DP Thoát Bài)", lambda: SamProShedderBot("SamProShedderBot", xin_sam_max_risk_pct=10.0)),
                ("SamRuleBot (Luật Truyền Thống)", lambda: SamRuleBot("SamRuleBot", xin_sam_max_risk_pct=5.0)),
                ("SamGreedyBot (Tham Lam)", lambda: SamGreedyBot("SamGreedyBot", xin_sam_max_risk_pct=0.0)),
            ],
            160,
        ),
        (
            "BÀN 4 NGƯỜI (4-PLAYER TABLE)",
            [
                ("SamSmartMathBot (AI Toán Học)", lambda: SamSmartMathBot("SamSmartMathBot", xin_sam_max_risk_pct=12.0)),
                ("SamProCounterBot (Đếm Bài)", lambda: SamProCounterBot("SamProCounterBot", xin_sam_max_risk_pct=8.0)),
                ("SamProShedderBot (DP Thoát Bài)", lambda: SamProShedderBot("SamProShedderBot", xin_sam_max_risk_pct=10.0)),
                ("SamRuleBot (Luật Truyền Thống)", lambda: SamRuleBot("SamRuleBot", xin_sam_max_risk_pct=5.0)),
            ],
            200,
        ),
        (
            "BÀN 3 NGƯỜI (3-PLAYER TABLE)",
            [
                ("SamSmartMathBot (AI Toán Học)", lambda: SamSmartMathBot("SamSmartMathBot", xin_sam_max_risk_pct=15.0)),
                ("SamProCounterBot (Đếm Bài)", lambda: SamProCounterBot("SamProCounterBot", xin_sam_max_risk_pct=10.0)),
                ("SamProShedderBot (DP Thoát Bài)", lambda: SamProShedderBot("SamProShedderBot", xin_sam_max_risk_pct=12.0)),
            ],
            250,
        ),
        (
            "BÀN 2 NGƯỜI SOLO (HEADS-UP 1v1)",
            [
                ("SamSmartMathBot (AI Toán Học)", lambda: SamSmartMathBot("SamSmartMathBot", xin_sam_max_risk_pct=18.0)),
                ("SamProCounterBot (Đếm Bài)", lambda: SamProCounterBot("SamProCounterBot", xin_sam_max_risk_pct=12.0)),
            ],
            350,
        ),
    ]

    for title, factories, deals in table_configs:
        print("\n" + "=" * 88)
        print(f"KẾT QUẢ ĐẤU TRƯỜNG DUPLICATE SÂM LỐC: {title} ({deals * len(factories)} VÁN)")
        print("=" * 88)
        res_stats = run_duplicate_sam_benchmark(factories, num_deals=deals)
        sorted_bots = sorted(res_stats.items(), key=lambda kv: -kv[1]["total_cards"])
        print(
            f"{'Hạng':<5} | {'Tên Bot':<32} | {'Tỷ Lệ Thắng':<13} | {'Xin Sâm (Ăn/Tổng)':<18} | {'Tổng Lá Thắng/Thua':<18}"
        )
        print("-" * 88)
        for rank_idx, (bname, st) in enumerate(sorted_bots, 1):
            wr = (st["wins"] / max(1, st["hands"])) * 100.0
            xs_str = f"{st['xin_sam_wins']}/{st['xin_sam_attempts']}"
            print(
                f"#{rank_idx:<4} | {bname:<32} | {wr:10.2f}%  | {xs_str:<18} | {st['total_cards']:+14d} lá"
            )

    print(f"\nHoàn tất toàn bộ kiểm định trong {time.time() - t0:.2f} giây.")


# ============================================================================
# [V4.8] SÂM BẢN CẢI TIẾN (tester_mode = "v48"): chế độ GIẢM THUA cho bài yếu, GIỮ BỘ CHẶN cho bài khá,
# BỘ GIẢI CUỐI VÁN khi đối thủ còn <= 3 lá (báo lỗi tester 30/10 baoloi_V4.7.0.txt, 9 ván).
# ============================================================================
def _sam_is_strong(m: SamCombo, unseen: Sequence[int]) -> bool:
    """Nhóm MẠNH = đối thủ khó chặn: heo, tứ quý, A lẻ, đôi K/A, sám từ 10 trở lên, sảnh không ai chặn được."""
    if m.is_pass:
        return False
    if m.is_all_twos or m.combo_type == SamComboType.FOUR_OF_KIND:
        return True
    r = m.order_value
    if m.combo_type == SamComboType.SINGLE:
        return r >= RANK_A
    if m.combo_type == SamComboType.PAIR:
        return r >= RANK_K
    if m.combo_type == SamComboType.TRIPLE:
        return r >= RANK_10
    if m.combo_type == SamComboType.STRAIGHT:
        return is_boss_sam_combo(m, unseen)
    return False


SAM_GROUPS_KEEP_SETS = True   # [V4.9.3] cùng số lượt -> chọn cách chia ít lá lẻ hơn (không xé đôi/sám ghép sảnh 3 lá)
SAM_LONG_STRAIGHT_MIN = 4     # [V4.9.3] luật "dồn sảnh dài nhất" (bài yếu) chỉ áp cho sảnh >= 4 lá
SAM_KEEP_STRONG_NO_BREAK = False   # [V4.9.4] luật V4.8 "không xé bộ mạnh chặn lẻ (bỏ lượt)": giữa ván −51 lá / 8 thế -> TẮT
SAM_MID_GAME_MAX_CARDS = 9    # [V4.9.4] tay <= 9 lá = giữa ván: luật mở bài V4.8/V4.9 nhường Monte Carlo (trừ heo trước + bộ khóa che)


def _sam_covered_weak(plan, unseen) -> List[SamCombo]:
    """[V4.9.4] Nhóm YẾU có BỘ KHÓA cùng loại + cùng số lá trong tay (bộ bất bại: heo lẻ, đôi 2, Q-K-A, sám to...):
    đối thủ chặn nhóm yếu thì mình lấy lại lượt bằng bộ khóa."""
    boss = [m for m in plan.combos if is_boss_sam_combo(m, unseen)]
    out = []
    for w in plan.combos:
        if w in boss or _sam_is_strong(w, unseen):
            continue
        if any(bb.combo_type == w.combo_type and len(bb.cards) == len(w.cards) and bb is not w for bb in boss):
            out.append(w)
    return out


def _partition_fewest_singles(hand: Sequence[int], max_turns: int) -> Optional[List[SamCombo]]:
    """[V4.9.3] Cách chia có số lượt <= max_turns và ÍT LÁ LẺ nhất (lá lẻ không tính A/2); bằng nhau ưu tiên ít sảnh 3 lá.
    Tester 31/10 (ván 09:14 [6 77 88 K AA], 10:33 [444 77 99 8 K A]): bot chia sảnh 6-7-8 / 7-8-9 + 2 lá lẻ thay vì 2 đôi
    -> luật rác-trước đánh lá vừa xé ra khỏi đôi."""
    cards = tuple(sorted(hand))
    multis = {}
    for c in generate_all_sam_combos(cards):
        if c.length >= 2:
            multis.setdefault(tuple(sorted(c.cards)), c)
    multis = sorted(multis.values(), key=lambda c: (-c.length, c.order_value))
    pos = {c: i for i, c in enumerate(cards)}
    best = [None, None]

    def key_of(chosen, left):
        singles = sum(1 for x in left if card_rank(x) < RANK_A)
        low_st = sum(1 for m in chosen if m.combo_type == SamComboType.STRAIGHT and m.length == 3)
        return (len(chosen) + len(left), singles, low_st)

    def dfs(i, used, chosen):
        left = [cards[k] for k in range(len(cards)) if not used >> k & 1]
        k = key_of(chosen, left)
        if k[0] <= max_turns and (best[0] is None or k < best[0]):
            best[0], best[1] = k, list(chosen)
        if len(chosen) + 1 > max_turns + 2:
            return
        for j in range(i, len(multis)):
            m = multis[j]
            mask = 0
            ok = True
            for c in m.cards:
                b = 1 << pos[c]
                if used & b:
                    ok = False
                    break
                mask |= b
            if ok:
                chosen.append(m)
                dfs(j + 1, used | mask, chosen)
                chosen.pop()

    dfs(0, 0, [])
    if best[1] is None:
        return None
    used = {c for m in best[1] for c in m.cards}
    out = list(best[1])
    for c in cards:
        if c not in used:
            r = card_rank(c)
            out.append(SamCombo(SamComboType.SINGLE, (c,), 1, r, f"Lẻ {RANK_NAMES[r]}"))
    return out


def _sam_groups(hand: Sequence[int], unseen: Sequence[int]):
    plan = optimal_partition_sam_hand(list(hand))
    combos = list(plan.combos)
    if SAM_GROUPS_KEEP_SETS and len(hand) >= 4:
        alt = _partition_fewest_singles(hand, plan.num_turns)
        n_single = lambda cs: sum(1 for m in cs if m.combo_type == SamComboType.SINGLE and m.order_value < RANK_A)
        if alt is not None and len(alt) <= len(combos) and n_single(alt) < n_single(combos):
            combos = alt
            plan = SamPartitionPlan(alt, len(alt), plan.free_turns, plan.trash_count, plan.boss_count,
                                    plan.only_twos_end_risk, plan.total_score)
    strong = [m for m in combos if _sam_is_strong(m, unseen)]
    weak = [m for m in combos if not _sam_is_strong(m, unseen)]
    return plan, strong, weak


def sam_weak_mode(hand: Sequence[int], strong: List[SamCombo], weak: List[SamCombo]) -> bool:
    """Bài KHÔNG có cửa về nhất (tester): nhóm yếu > nhóm mạnh + 1, hoặc = nhóm mạnh + 1 mà không có heo."""
    has2 = any(card_rank(c) == RANK_2 for c in hand)
    return len(weak) > len(strong) + 1 or (len(weak) == len(strong) + 1 and not has2)


_V48_BRANCH = [""]   # nhánh luật vừa quyết (để đo / log)
SAM_TESTER_HEO_RAC = False   # [V4.9.30 TẮT] tránh ép đánh rác/heo cứng sau MC gây thối heo và mất cái nặng (ván 22:07:53, 19:36:59)
SAM_SAFE_HEO = False
SAM_SAFE_HEO_LEAD_EV = None
SAM_SAFE_HEO_RESP_EV = -3.0
SAM_SAFE_HEO_LEAD_MAX = 7
SAM_SAFE_HEO_LEAD_OPP_MAX = 7
SAM_HEO_SOM_BAI_YEU = False     # [V4.9.30 TẮT]
SAM_HEO_SOM = False             # [V4.9.30 TẮT]
SAM_SMART_MID_BEAT = False
SAM_TESTER_HEO_RAC_BLOCK = False
SAM_6D6_DOI_THUONG = False
SAM_TESTER_MULTI_FIRST = False
SAM_LEAD_LONG_STRAIGHT = False  # [V4.9.30 TẮT]
SAM_RAC_TRUOC_8LA = False       # [V4.9.30 TẮT]
SAM_TESTER_WEAK_DUMP = False    # [V4.9.30 TẮT]


def _sam_mc_ev_best():
    return getattr(_SAM_MC_RANK, "ev_best", None)


_SAM_MC_RANK = threading.local()   # [V4.9.7] thứ hạng Monte Carlo của nước THẬT (chỉ đặt quanh lần gọi luật ở nước thật, không ở mô phỏng)


def _sam_pick_by_mc(cands: List[SamCombo]) -> SamCombo:
    """Trong nhóm nước tester cho phép (vd các lá rác), chọn nước Monte Carlo xếp cao nhất; không có thứ hạng -> lá nhỏ nhất."""
    rank = getattr(_SAM_MC_RANK, "rank", None) or []
    order = {}
    for i, m in enumerate(rank):
        order.setdefault((m.is_pass, m.combo_type, tuple(sorted(card_rank(c) for c in m.cards))), i)
    return min(cands, key=lambda m: (order.get((m.is_pass, m.combo_type, tuple(sorted(card_rank(c) for c in m.cards))), 10 ** 6),
                                     m.order_value))


def _sam_n_ctrl(hand: Sequence[int], plan) -> int:
    """[V4.9.27] Số lá GIÀNH LƯỢT rời: A/2 không nằm trong sảnh >= 4 lá của cách xếp bài (A trong J-Q-K-A không tính;
    A-2-3 ghép tạm 3 lá vẫn tính vì người thật giữ A/2 làm lá giành lượt và coi 3 là rác)."""
    locked = set()
    for m in plan.combos:
        if m.combo_type == SamComboType.STRAIGHT and len(m.cards) >= 4:
            locked.update(m.cards)
    return sum(1 for c in hand if card_rank(c) >= RANK_A and c not in locked)


def _sam_low_junk(hand: Sequence[int]) -> List[SamCombo]:
    """Lá RÁC theo tester: xếp bài KHÔNG tính A/2 (A/2 là bài giành cái), lá lẻ còn lại là rác."""
    low = [c for c in hand if card_rank(c) < RANK_A]
    if not low:
        return []
    return [m for m in optimal_partition_sam_hand(low).combos if m.combo_type == SamComboType.SINGLE]


def _sam_v48_adjust(state: "SamTableState", base: SamCombo) -> SamCombo:
    """Luật V4.8 lên nước gốc (đối thủ còn > 3 lá; <= 3 lá để bộ giải cuối ván quyết):
    - Cầm lượt, bài YẾU: tống nhóm yếu NHIỀU LÁ NHẤT (sảnh dài...), không có thì lá rác nhỏ nhất.
    - Cầm lượt, bài KHÁ: còn rác thì đánh lá rác nhỏ nhất; KHÔNG mở bằng bộ mạnh (giữ làm bộ chặn / bộ về cuối).
    - Bài YẾU, đối thủ đánh lẻ, mình có heo: dùng heo lấy lượt ngay (không giữ heo tới cuối -> thối).
    - Bài KHÁ: không xé bộ mạnh (đôi K/A, sám cao) để chặn 1 lá lẻ khi đối thủ còn nhiều lá."""
    _V48_BRANCH[0] = "base"
    if state.xin_sam_player is not None:
        return base
    sel = getattr(_SAM_MC_RANK, "rule_set", "full") == "chon_loc"   # [V4.9.13 A/B] bộ luật chọn lọc: bỏ nhóm "giữ heo đánh rác"
    if int(getattr(state, "num_players", 2) or 2) > 2:
        _V48_BRANCH[0] = "mc_nhieu_nguoi"   # [V4.9.17] bàn >= 3 người: luật học từ bàn 2 người không áp, Monte Carlo quyết
        return base
    if getattr(_SAM_MC_RANK, "rule_set", "full") == "mc":
        _V48_BRANCH[0] = "mc"   # [V4.9.14 A/B nhánh C] Monte Carlo thuần: không áp lớp luật V4.8-V4.9 (bộ giải cuối ván vẫn chạy)
        return base
    hand = list(state.my_hand)
    opp_n = state.min_opponent_cards
    if opp_n <= 3 or len(hand) <= 1:
        return base
    unseen = _sam_unseen(state)
    plan, strong, weak = _sam_groups(hand, unseen)
    legal = get_legal_sam_moves(hand, state.board_combo, state.next_player_card_count)
    keys = {tuple(sorted(m.cards)): m for m in legal}
    weak_mode = sam_weak_mode(hand, strong, weak)
    b = state.board_combo
    if b is None or b.is_pass:
        # [V4.9.27] P2: lá giành lượt = A/2 RỜI hoặc đôi A/2 (xé được); A/2 nằm trong sảnh không tính (người thật: A trong sảnh -> chạy sảnh 72%)
        _n_ctrl = _sam_n_ctrl(hand, plan)
        if (SAM_HEO_SOM_BAI_YEU and len(hand) >= 8 and weak_mode and opp_n >= 8 and not sel
                and _n_ctrl == 1 and sum(1 for c in hand if card_rank(c) == RANK_2) == 1
                and not any(m.combo_type == SamComboType.STRAIGHT and len(m.cards) >= 5 and _sam_is_strong(m, unseen) for m in legal)):
            # [V4.9.29] BÀI YẾU + lá giành lượt rời DUY NHẤT là 1 lá 2 + CÓ CÁI: ra 2 trước (ăn chắc, thoát khoản phạt −9), rác / bộ đánh sau.
            # Có thêm A rời (như ván 13:22) thì không áp: còn A để giành lại lượt, mở rác theo mục 14. Xem chú thích patch_v4929.py.
            _two1 = [m for m in legal if m.combo_type == SamComboType.SINGLE and m.is_all_twos]
            if _two1:
                _V48_BRANCH[0] = "ĐI heo sớm bài yếu: >= 8 lá, 1 heo, không cửa giành lại lượt -> ra 2 trước"
                return _two1[0]
        if SAM_RAC_TRUOC_8LA and len(hand) >= 8 and _n_ctrl >= 1 and not sel:
            # [V4.9.24] MỤC 14: đầu ván còn A/2 -> xả rác lẻ trước, giữ sảnh/đôi (người thắng: lẻ 9-K 96%, lẻ nhỏ 74%, sảnh 4 73%, đôi 55-79%)
            _junk = sorted((m for m in plan.combos if m.combo_type == SamComboType.SINGLE and m.order_value < RANK_A),
                           key=lambda m: m.order_value)
            _hard5 = any(m.combo_type == SamComboType.STRAIGHT and len(m.cards) >= 5 and _sam_is_strong(m, unseen) for m in legal)
            if _junk and not _hard5 and not (base.combo_type == SamComboType.SINGLE and base.is_all_twos):
                _mid = [m for m in _junk if RANK_9 <= m.order_value <= RANK_K]
                # [V4.9.27] P1: 1 lá giành lượt (một 2 hoặc một A) -> rác NHỎ NHẤT (người: 23 lượt 57% vs 9-K 2 lượt; tester ván 16:59, 15:59);
                # >= 2 lá giành lượt -> rác 9-K THẤP nhất (người: 8 lượt 88% vs nhỏ 12 lượt 58%)
                _pick = (_mid[0] if (_mid and _n_ctrl >= 2 and any(card_rank(c) == RANK_2 for c in hand)) else _junk[0])   # [V4.9.28] L3: chỉ có A -> rác nhỏ nhất (người 8 lượt 62%; ván 16:33)
                mv = keys.get(tuple(sorted(_pick.cards)))
                if mv is not None:   # [V4.9.28] trả về cả khi MC đã chọn đúng lá, để luật phía sau không đổi lại
                    _V48_BRANCH[0] = "ĐI tester 13:22: còn A/2 -> rác lẻ trước, sảnh/đôi để sau"
                    return mv
        if len(hand) <= 7 and not sel and sum(1 for c in hand if card_rank(c) == RANK_2) == 1:
            # [V4.9.28/V4.9.31/V5.0] L1: tay = 1 lá 2 rời + đúng 1 bộ (+ tối đa 1 lá lẻ S):
            # - Nếu bộ M là sảnh dài mạnh (>= 4 lá, >= J, hoặc bất bại / Effective Boss khi đối thủ đã bỏ qua bộ cùng loại)
            #   và S là rác nhỏ (< Q): đánh M trước, rồi 2, S về cuối (VD ván 11:08:50 [6♦, 9-K, 2♦]).
            # - Ngược lại (M yếu dễ bị chặn như Đôi 4 ván 16:12:58 [44 A 2], hoặc S >= Q như L1b [5-9 Q 2]): đánh S trước (có 2 bọc lẻ), rồi 2, bộ M về cuối!
            _pass_caps_v48 = _extract_sam_opp_pass_caps(state)
            _grp = [m for m in plan.combos if len(m.cards) >= 2]
            _sg = [m for m in plan.combos if m.combo_type == SamComboType.SINGLE]
            _two1 = [m for m in _sg if card_rank(m.cards[0]) == RANK_2]
            _jk = sorted((m for m in _sg if card_rank(m.cards[0]) != RANK_2), key=lambda m: m.order_value)
            if len(_grp) == 1 and len(_two1) == 1 and (
                len(_jk) <= 1
                or (
                    not _is_effective_boss_sam_combo(_grp[0], unseen, _pass_caps_v48)
                    and (
                        (_grp[0].combo_type == SamComboType.PAIR and _grp[0].order_value <= RANK_8)
                        or (_grp[0].combo_type == SamComboType.STRAIGHT and len(_grp[0].cards) == 3 and _grp[0].order_value <= RANK_7)
                        or (len(hand) <= 7 and _grp[0].combo_type == SamComboType.STRAIGHT and len(_grp[0].cards) <= 4 and _grp[0].order_value <= 3)
                        or (
                            sum(1 for m in _jk if m.order_value < RANK_A) <= 1 + sum(1 for m in _jk if m.order_value == RANK_A)
                            and (
                                (_grp[0].combo_type == SamComboType.PAIR and _grp[0].order_value <= RANK_Q)
                                or (_grp[0].combo_type == SamComboType.STRAIGHT and len(_grp[0].cards) == 3 and _grp[0].order_value <= RANK_10)
                            )
                        )
                    )
                )
            ):
                _m_cb = _grp[0]
                _m_strong_lead = (
                    _is_effective_boss_sam_combo(_m_cb, unseen, _pass_caps_v48)
                    or (
                        _m_cb.combo_type == SamComboType.STRAIGHT
                        and (
                            (len(_m_cb.cards) >= 4 and _m_cb.order_value >= RANK_9)
                            or (_m_cb.order_value >= RANK_J and (not _jk or _jk[0].order_value <= RANK_6))
                        )
                    )
                    or (
                        _m_cb.combo_type == SamComboType.TRIPLE
                        and _m_cb.order_value >= RANK_7
                        and (not _jk or _jk[0].order_value <= RANK_6)
                    )
                )
                if _jk and _m_strong_lead and _jk[0].order_value < RANK_Q:
                    _tgt = _m_cb
                else:
                    _tgt = _jk[0] if _jk else _two1[0]
                _mvL1 = keys.get(tuple(sorted(_tgt.cards)))
                if _mvL1 is not None and not would_leave_only_twos(hand, _mvL1):
                    _V48_BRANCH[0] = "ĐI L1: " + (
                        "bộ mạnh trước, giữ 2, rác về cuối" if _tgt is _m_cb
                        else ("rác trước, giữ 2, bộ về cuối" if _jk else "2 trước, bộ về cuối")
                    )
                    return _mvL1
        if SAM_HEO_SOM and len(hand) <= 7 and not sel:
            # [V4.9.28] HEO SỚM (theo TIỀN người thật, mọi mức bài đối thủ): có cái <= 7 lá mà còn heo -> ra heo trước, không mở rác giữ heo.
            # Thối heo = 31% tổng lỗ Sâm; luật cũ "bài bé có heo -> rác trước" chính là nhóm mở rác (+2,0..3,2) thay vì heo (+4,7..10,5).
            # Ngoại lệ: có sảnh >= 5 lá chắc ăn (người thật +5,9..9,5, ngang heo) -> để luật sảnh dài quyết.
            _twos = [m for m in legal if m.combo_type == SamComboType.SINGLE and m.is_all_twos]
            _s5 = any(m.combo_type == SamComboType.STRAIGHT and len(m.cards) >= 5 and _sam_is_strong(m, unseen) for m in legal)
            if _twos and not _s5:
                _V48_BRANCH[0] = "ĐI heo sớm: có cái <= 7 lá -> ra heo trước (tiền người thật)"
                return min(_twos, key=lambda m: m.cards)
        return base
        if SAM_LEAD_LONG_STRAIGHT:
            # [V4.9.11] TESTER 01/11 (4 ván 23:06, 11:09, 11:29, 11:34): CÓ CÁI (nhất là vừa đốt A/2 giành được) -> CHẠY SẢNH DÀI ngay,
            # không đánh lẻ/đôi nhỏ vu vơ rồi mất cái; K/A giữ để chặn, rác nhỏ để sau. Người thật 1.576 ván: có cái giữa ván dẫn sảnh 4-5
            # thắng 84-86% vs đôi/rác nhỏ 57-60%. Áp: sảnh >= 5 lá luôn; sảnh 4 khi khó chặn, hoặc không còn A/2 giữ cái, hoặc tay <= 8 lá
            # (cầm heo mà tay <= 7: chỉ khi sảnh khó chặn, còn lại để luật an toàn heo quyết).
            sts = [m for m in legal if m.combo_type == SamComboType.STRAIGHT and len(m.cards) >= 4
                   and not any(card_rank(c) == RANK_2 for c in m.cards)]
            if sts:
                best_s = max(sts, key=lambda m: (len(m.cards), -m.order_value))   # [V4.9.27] P3: bằng độ dài -> sảnh THẤP trước, sảnh cao để che (tester ván 17:26)
                has_two = any(card_rank(c) == RANK_2 for c in hand)
                has_ctrl = any(card_rank(c) >= RANK_A for c in hand)
                hard = _sam_is_strong(best_s, unseen)
                ok = (len(best_s.cards) >= 5 and (hard or not has_two)) or hard or not has_ctrl or len(hand) <= 8
                if len(hand) >= 8 and not (len(best_s.cards) >= 5 and hard):
                    ok = False   # [V4.9.25] 6d-3: >= 8 lá người thắng chạy sảnh 3 thấp / rác trước, giữ sảnh 4 (81% / 80% vs 61% / 53%)
                if has_two and not hard and opp_n <= 4:
                    ok = False   # ĐT sắp về: sảnh dễ chặn mà bị chặn là thối heo -> để luật an toàn heo quyết
                if has_two and not hard and len(hand) >= 9:
                    ok = False   # ván tester 21:45:47 [5-9 88 99 K 22]: sảnh 5-9 bị 7-J chặn; còn 2 heo + K thì chưa vội, rác/đôi trước (+10 vs −1)
                if ok:
                    _V48_BRANCH[0] = "ĐI tester 01/11: có cái -> chạy sảnh dài trước"
                    return best_s
            # sám trước lá lẻ / sảnh 3 dễ chặn khi tay <= 8 lá (tester 31/10 12:35: sám Q -> sảnh 8-9-10 -> K -> 10 cuối;
            # tester 30/10 16:15 lỗi 2: còn [3-4-5 | 7 | sám 10], ĐT 4 lá -> sám 10 (chắc) trước, sảnh 3-4-5 (rủi ro) sau)
            risky_base = ((base.combo_type == SamComboType.SINGLE and not base.is_all_twos and base.order_value < RANK_A)
                          or (base.combo_type == SamComboType.STRAIGHT and len(base.cards) == 3 and not _sam_is_strong(base, unseen)))
            if len(hand) <= 7 and risky_base:   # [V4.9.25] 6d-1: ở 8 lá người thắng mở lẻ 79% vs sám 39% (31 lượt) -> sám trước chỉ từ 7 lá
                trips = [m for m in legal if m.combo_type == SamComboType.TRIPLE and not m.is_all_twos]
                if trips:
                    _V48_BRANCH[0] = "ĐI tester 12:35: sám trước lá lẻ/sảnh 3"
                    return max(trips, key=lambda m: m.order_value)
        # [V4.9.30] Nhường cho Monte Carlo và Định lý về đích 2-Combo xử lý tay 2-5 lá (tránh xé sảnh A-2-3-4-5 hoặc Đôi 2)
        if SAM_TESTER_HEO_RAC:
            # [V4.9.7] TƯ DUY TESTER (31/10 ván 09:17, 15:19:47, 21:05): có cái, bài bé (không có bộ mạnh) mà cầm heo -> chạy RÁC lẻ nhỏ
            # nhất trước (đối thủ đè thì heo giật lại cái + thoát heo); KHÔNG mở đôi bé (bị chặn là mất cái, heo lẻ không cứu được đôi).
            # Hết rác mà heo còn -> ra heo ngay khi có cái, trước mọi bộ khác.
            twos = [m for m in legal if m.combo_type == SamComboType.SINGLE and m.is_all_twos]
            strong_multi = [m for m in strong if len(m.cards) >= 2 and not m.is_all_twos]
            if twos and sum(1 for c in hand if card_rank(c) == RANK_2) >= 3:
                # [V4.9.10] cầm >= 3 heo: ra 1 heo ngay khi có cái (ván V4.9.8 042825 [345 8 9 J Q 222] mở rác -> thối 3 heo −39;
                # heo trước −3). Còn 2 heo chống lưng nên không mất quyền kiểm soát.
                _V48_BRANCH[0] = "ĐI an toàn: >= 3 heo -> ra bớt heo"
                return min(twos, key=lambda m: m.cards)
            if twos:
                junk = _sam_low_junk(hand)
                opts = [keys[tuple(sorted(j.cards))] for j in junk if tuple(sorted(j.cards)) in keys]
                if opts and not strong_multi:
                    # [V4.9.9] AN TOÀN (người dùng chọn): có cái mà cầm heo -> ra heo trước LUÔN, rác sau. Gate theo Monte Carlo
                    # ("thế không chắc thắng") không bắt được 7/8 ván thối heo V4.9.8 vì lúc đó MC tưởng đang thắng; giá: 37 thế thật
                    # rác hơn heo +90 / heo hơn rác +51 (3 ván thối ≥10 lá nằm trong đó) -> chấp nhận kém ~1 lá/thế để hết thối kiểu này.
                    ev = _sam_mc_ev_best()
                    # [V4.9.10] chỉ "an toàn heo" khi mình <= 7 lá VÀ đối thủ <= 7 lá (người thật: >= 8 lá không ai dẫn heo)
                    if (SAM_SAFE_HEO and len(hand) <= SAM_SAFE_HEO_LEAD_MAX and opp_n <= SAM_SAFE_HEO_LEAD_OPP_MAX
                            and (SAM_SAFE_HEO_LEAD_EV is None or ev is None or ev < SAM_SAFE_HEO_LEAD_EV)):
                        pair2 = [m for m in legal if m.combo_type == SamComboType.PAIR and m.is_all_twos]
                        _V48_BRANCH[0] = "ĐI an toàn: cầm heo -> heo trước"
                        return pair2[0] if pair2 else min(twos, key=lambda m: m.cards)
                    if not sel:   # [A/B] chọn lọc: không ép rác trước (log thật −1,41 lá/lượt), để Monte Carlo
                        _mid = [m for m in opts if RANK_9 <= m.order_value <= RANK_K]
                        _nc = _sam_n_ctrl(hand, plan)
                        if len(hand) >= 8 and opts:
                            # [V4.9.27] P1: >= 8 lá: 1 lá giành lượt -> rác nhỏ nhất; >= 2 -> rác 9-K thấp nhất (không để Monte Carlo chọn K)
                            _V48_BRANCH[0] = "ĐI tester: bài bé có heo -> rác trước [P1]"
                            return min(_mid, key=lambda m: m.order_value) if (_mid and _nc >= 2) else min(opts, key=lambda m: m.order_value)
                        if _mid and 5 <= len(hand) <= 7:
                            # [V4.9.26] 6d-7: 5-7 lá còn heo, người thắng mở rác 9-K (8 lượt 100%) thay vì rác nhỏ nhất (40 lượt 75%)
                            _V48_BRANCH[0] = "ĐI tester: bài bé có heo -> rác 9-K trước [6d-7]"
                            return min(_mid, key=lambda m: m.order_value)
                        _V48_BRANCH[0] = "ĐI tester: bài bé có heo -> rác trước"
                        return _sam_pick_by_mc(opts)
                if not junk:
                    # [V4.9.9] kể cả khi có bộ mạnh: hết rác mà heo còn -> ra heo ngay khi có cái (tester 15:19:47; log V4.9.8 ván 002806
                    # [33 7-10 KK 2♣]: heo +17, sảnh 7-10 −15). Có đôi heo thì đánh cả đôi.
                    pair2 = [m for m in legal if m.combo_type == SamComboType.PAIR and m.is_all_twos]
                    _V48_BRANCH[0] = "ĐI tester: hết rác -> heo trước"
                    return pair2[0] if pair2 else min(twos, key=lambda m: m.cards)
        if SAM_TESTER_MULTI_FIRST and len(hand) <= 7 and opp_n >= 4:
            multi = [m for m in legal if len(m.cards) >= 2 and not m.is_all_twos]
            if multi and base.combo_type == SamComboType.SINGLE and not base.is_all_twos and base.order_value < RANK_A:
                strong_keys = {tuple(sorted(m.cards)) for m in strong if len(m.cards) >= 2}
                sure = [m for m in multi if tuple(sorted(m.cards)) in strong_keys]
                _V48_BRANCH[0] = "ĐI tester 12:35: bộ nhiều lá trước, lá lẻ nhỏ để cuối"
                return max(sure or multi, key=lambda m: (len(m.cards), -m.order_value))
        if SAM_TESTER_WEAK_DUMP and weak_mode and len(hand) >= 6 and not sel:
            wm = [keys[tuple(sorted(m.cards))] for m in weak if len(m.cards) >= 2 and tuple(sorted(m.cards)) in keys]
            if len(hand) >= 8:
                wm = [m for m in wm if len(m.cards) >= 4]   # [V4.9.25] 6d-2: >= 8 lá không tống sảnh 3 / đôi trước (người: đôi 55% vs sảnh 3 39%)
            if wm and (base.combo_type == SamComboType.SINGLE or len(base.cards) < max(len(m.cards) for m in wm)):
                _V48_BRANCH[0] = "ĐI tester 16:15: bài yếu -> tống nhóm yếu nhiều lá nhất"
                return max(wm, key=lambda m: (len(m.cards), -m.order_value))
        if not weak or len(plan.combos) <= 2:
            return base
        if len(hand) <= SAM_MID_GAME_MAX_CARDS:
            # [V4.9.4] GIỮA VÁN (tay <= 9 lá): bộ giải biết hết bài trên 1.271 lượt được đi thật -> các luật mở bài V4.8/V4.9
            # (bài khá rác nhỏ nhất −115, bài yếu nhóm nhiều lá −49, rác trước −17, dồn sảnh −16) KÉM Monte Carlo -> để Monte Carlo quyết.
            # Chỉ thêm "BỘ KHÓA CHE" cho bài YẾU (tester 31/10 ván 15:19 lẻ có heo che, 12:57 sảnh 3 có Q-K-A che): +113 lá / 157 thế.
            return base
            return base
        return base
    if (SAM_6D6_DOI_THUONG and b.combo_type == SamComboType.PAIR and not b.is_all_twos and base.combo_type == SamComboType.PAIR and base.is_all_twos
            and len(hand) >= 8 and opp_n >= 4 and not sel):
        # [V4.9.26] 6d-6: đỡ đôi đầu ván cầm 2 heo: người thắng đè bằng đôi thường 37/44 lần (68%, ĐT 5-7 lá 91%), giữ đôi heo làm bộ kiểm soát
        _pairs = [m for m in legal if m.combo_type == SamComboType.PAIR and not m.is_all_twos]
        if _pairs:
            _V48_BRANCH[0] = "CHẶN 6d-6: đỡ đôi bằng đôi thường, giữ đôi heo"
            return min(_pairs, key=lambda m: m.order_value)
    if SAM_TESTER_HEO_RAC and b.combo_type == SamComboType.SINGLE and not b.is_all_twos and len(hand) >= 4:
        twos = [m for m in legal if m.combo_type == SamComboType.SINGLE and m.is_all_twos]
        if twos and SAM_SAFE_HEO:
            ev = _sam_mc_ev_best()
            n_two_all = sum(1 for c in hand if card_rank(c) == RANK_2)
            if ev is not None and ev <= SAM_SAFE_HEO_RESP_EV:
                _V48_BRANCH[0] = "CHẶN an toàn: thế đang thua -> đè bằng heo, không ôm"
                return min(twos, key=lambda m: m.cards)
            _jb = {j.cards[0] for j in _sam_low_junk(hand)}
            _jb = [m for m in legal if m.combo_type == SamComboType.SINGLE and not m.is_all_twos and m.cards[0] in _jb]
            if n_two_all >= 2 and not sel:   # [V4.9.28] L2 KHÔNG cài: theo tiền, >= 2 heo mà MC muốn heo thì heo +4,3 vs rác +1,8..3,8 cược/ván
                # [V4.9.28] L2: >= 8 lá, đối thủ >= 5 lá, có rác đè được -> KHÔNG dùng heo (người thật >= 2 heo: đè rác 82-90% vs heo 76%, 146 vs 92 lượt);
                # rơi xuống luật "rác nhiều -> đè bằng rác nhỏ nhất, giữ heo"
                # [V4.9.9] AN TOÀN: >= 2 heo thì dùng 1 heo giành cái ngay (còn heo kia chống lưng); 49 thế thật: heo hơn nước thật +29 lá
                # (ván thối 050908: đè 7♠ bằng 10♥ −28, bằng heo −1)
                _V48_BRANCH[0] = "CHẶN an toàn: >= 2 heo -> heo giành cái"
                return min(twos, key=lambda m: m.cards)
        if twos:
            strong_multi = [m for m in strong if len(m.cards) >= 2 and not m.is_all_twos]
            junk = _sam_low_junk(hand)
            jc = {j.cards[0] for j in junk}
            beat = [m for m in legal if m.combo_type == SamComboType.SINGLE and m.cards[0] in jc]
            n_two = sum(1 for c in hand if card_rank(c) == RANK_2)
            if SAM_TESTER_HEO_RAC_BLOCK and len(junk) >= 2 and beat and (n_two >= 2 or not strong_multi) and opp_n >= 5 and not sel:
                # [V4.9.11] chỉ khi đối thủ còn >= 5 lá (người thật: ĐT <= 4 lá thì đè bằng heo thắng 74% vs rác 69%; ván V4.9.10 11:28
                # đè 4♦ bằng 9♥ khi ĐT 5 lá -> bị 2♦ đè, kẹt 7 lá thối heo; bộ giải: heo −4, rác −17)
                # [V4.9.7] tester 31/10 ván 21:00: rác nhiều, có A/2 giành lại cái được -> đè bằng RÁC, giữ heo (không đem bài to ra sớm)
                # [V4.9.8] có >= 2 heo thì vẫn đè bằng rác dù có bộ mạnh (ván 21:45:07 [44 6 7 Q KK A 2 2]: rác +7, heo +1 / −2)
                _V48_BRANCH[0] = "CHẶN tester: rác nhiều -> đè bằng rác nhỏ nhất, giữ heo [P4]"
                return min(beat, key=lambda m: m.order_value)   # [V4.9.27] P4: lá rác NHỎ NHẤT đè được (người 38/44; ván 16:22 đè K♥ rồi ôm 2♥)
            if SAM_SMART_MID_BEAT and n_two == 1 and len(junk) >= 3 and beat and opp_n >= 5 and not sel:
                # [V4.9.10] người thật, 1 heo + bộ mạnh, đối thủ ra lẻ thường, tách theo số rác: rác >= 3 -> heo thắng 33-47%,
                # đè bằng rác 62-80% (9-K tốt nhất); rác <= 2 (bài gần toàn bộ mạnh, như ván tester 10:17) -> heo 79-84% = giữ luật heo.
                # [V4.9.26] 6d-5: so cùng tay bài, người thắng đè bằng lá rác NHỎ NHẤT đè được (38/44 lần, 63% vs 9-K 33%) -> bỏ ưu tiên 9-K
                _V48_BRANCH[0] = "CHẶN khôn: 1 heo, rác >= 3 -> đè bằng rác nhỏ nhất, giữ heo [6d-5]"
                return min(beat, key=lambda m: m.order_value)
            if strong_multi:
                # [V4.9.7] tester 31/10 ván 10:17: 1 heo + BỘ MẠNH (sám 10...) chỉ thiếu cái -> dùng heo giành cái rồi chạy bộ
                # (bộ giải: heo −2, rác K −15)
                _V48_BRANCH[0] = "CHẶN tester: có bộ mạnh -> heo giành cái"
                return min(twos, key=lambda m: m.cards)
    # [V4.9.30] Bỏ nhánh ép chặn bằng Heo ở đầu ván / bài yếu để tránh nộp Heo vào Tứ quý hoặc xé Sám 2 / Đôi 2
    if (SAM_KEEP_STRONG_NO_BREAK and not weak_mode and not base.is_pass and b.combo_type == SamComboType.SINGLE and opp_n >= 5
            and base.combo_type == SamComboType.SINGLE and len(hand) > SAM_MID_GAME_MAX_CARDS):
        # [V4.9.4] chỉ đầu ván (10 lá): giữa ván luật này −51 lá / 8 thế (bộ giải biết hết bài)
        strong_multi = [set(m.cards) for m in strong if len(m.cards) >= 2 and not m.is_all_twos]
        if any(set(base.cards) & s for s in strong_multi) and PASS_COMBO in legal:
            _V48_BRANCH[0] = "CHẶN: không xé bộ mạnh (bỏ)"
            return PASS_COMBO
    return base



def _sam_6d_sanh3_filter(state: "SamTableState", mv: SamCombo) -> SamCombo:
    """[V4.9.30 TẮT] Không tự ý đổi sảnh 3 của Monte Carlo sang đôi K/rác lẻ (sửa lỗi ván 19:12:42, 18:36:36, 18:57:33)."""
    return mv
    try:
        if mv is None or mv.is_pass or mv.combo_type != SamComboType.STRAIGHT or len(mv.cards) != 3:
            return mv
        if state.xin_sam_player is not None or int(getattr(state, "num_players", 2) or 2) > 2:
            return mv
        if getattr(_SAM_MC_RANK, "rule_set", "full") in ("mc", "chon_loc"):
            return mv
        b = state.board_combo
        if b is not None and not b.is_pass:
            return mv
        hand = list(state.my_hand)
        if len(hand) < 5 or state.min_opponent_cards <= 3:
            return mv
        if any(card_rank(c) == RANK_2 for c in mv.cards):
            return mv
        unseen = _sam_unseen(state)
        if _sam_is_strong(mv, unseen):
            return mv
        plan, _strong, _weak = _sam_groups(hand, unseen)
        legal = get_legal_sam_moves(hand, None, state.next_player_card_count)
        keys = {tuple(sorted(m.cards)): m for m in legal}
        junk = sorted((m for m in plan.combos if m.combo_type == SamComboType.SINGLE and m.order_value < RANK_A),
                      key=lambda m: m.order_value)
        pairs = sorted((m for m in plan.combos if m.combo_type == SamComboType.PAIR and not m.is_all_twos and m.order_value < RANK_A),
                       key=lambda m: m.order_value)
        pick, tag = None, ""
        if len(hand) >= 8 and pairs:
            pick, tag = keys.get(tuple(sorted(pairs[0].cards))), "đôi thường"
        if pick is None and junk:
            pick, tag = keys.get(tuple(sorted(junk[0].cards))), "rác lẻ"
        if pick is None or tuple(sorted(pick.cards)) == tuple(sorted(mv.cards)):
            return mv
        _V48_BRANCH[0] = f"ĐI 6d: sảnh 3 không mở khi còn {tag} ({len(hand)} lá)"
        return pick
    except Exception:
        return mv

# ---------------------------------------------------------------- bộ giải cuối ván (2 người)
def _rank_counts(cards: Sequence[int]) -> Tuple[int, ...]:
    c = [0] * 13
    for x in cards:
        c[card_rank(x)] += 1
    return tuple(c)


def _concrete(counts: Tuple[int, ...]) -> List[int]:
    out = []
    for r, k in enumerate(counts):
        out.extend(r * 4 + s for s in range(k))
    return out


def _sub_counts(counts: Tuple[int, ...], cards: Sequence[int]) -> Tuple[int, ...]:
    c = list(counts)
    for x in cards:
        c[card_rank(x)] -= 1
    return tuple(c)


def _combo_key(m: Optional[SamCombo]):
    if m is None or m.is_pass:
        return None
    return (int(m.combo_type), m.length, m.order_value)


def _loss_of(counts: Tuple[int, ...], rule: "SamRuleConfig") -> int:
    n = sum(counts)
    return n + counts[RANK_2] * rule.thoi_two + sum(1 for k in counts if k == 4) * rule.thoi_four


class _SamEndgame:
    """Minimax biết hết bài (2 người) trên SỐ LƯỢNG lá theo rank (Sâm không so chất). Giá trị = lá thắng/thua của MÌNH."""

    def __init__(self, rule: "SamRuleConfig", deadline: float):
        self.rule = rule
        self.deadline = deadline
        self.memo: Dict[tuple, float] = {}
        self.legal_cache: Dict[tuple, List[SamCombo]] = {}

    def legal(self, counts, board, other_n):
        key = (counts, _combo_key(board), other_n)
        mv = self.legal_cache.get(key)
        if mv is None:
            raw = get_legal_sam_moves(_concrete(counts), board, other_n, strict_bao_mot=True)
            seen, mv = set(), []
            for m in raw:
                k2 = (_combo_key(m), _rank_counts(m.cards))
                if k2 not in seen:
                    seen.add(k2)
                    mv.append(m)
            self.legal_cache[key] = mv
        return mv

    def play(self, hands, m, board, turn):
        """Giá trị sau khi người `turn` đánh m (khác PASS)."""
        new = _sub_counts(hands[turn], m.cards)
        chop = 0
        if board is not None and board.combo_type == SamComboType.SINGLE and board.is_all_twos \
                and m.combo_type == SamComboType.FOUR_OF_KIND:
            chop = self.rule.chop_two
        sign = 1 if turn == 0 else -1
        if sum(new) == 0:
            if m.is_all_twos:
                return sign * (chop - self.rule.finish_two_penalty)
            return sign * (chop + _loss_of(hands[1 - turn], self.rule))
        nh = (new, hands[1]) if turn == 0 else (hands[0], new)
        return sign * chop + self.solve(nh, m, turn, 1 - turn)

    def solve(self, hands, board, owner, turn):
        key = (hands, _combo_key(board), owner, turn)
        v = self.memo.get(key)
        if v is not None:
            return v
        if time.monotonic() > self.deadline:
            raise TimeoutError
        moves = self.legal(hands[turn], board, sum(hands[1 - turn]))
        best = None
        for m in moves:
            if m.is_pass:
                val = self.solve(hands, None, None, owner)
            else:
                val = self.play(hands, m, board, turn)
            if best is None or (val > best if turn == 0 else val < best):
                best = val
        if best is None:  # không có nước (không xảy ra) -> bỏ lượt
            best = self.solve(hands, None, None, owner) if board is not None else 0.0
        self.memo[key] = best
        return best


# [V4.9] Bài đối thủ (người thật) lúc còn 1-3 lá KHÔNG chia đều: đo trên log thật ~1.100 ván Sâm HIT (lá thật / kỳ vọng chia đều).
# Còn 1 lá: không bao giờ là 2 (về bằng 2 bị phạt); còn 2-3 lá: ít 2 hơn (x0.75), nhiều A (x1.4-1.5), K/Q (x1.25).
SAM_ENDGAME_OPP_PRIOR: Dict[int, Dict[int, float]] = {
    1: {RANK_2: 0.0, RANK_A: 0.75},
    2: {RANK_2: 0.77, RANK_A: 1.37, RANK_K: 1.26},
    3: {RANK_2: 0.75, RANK_A: 1.5, RANK_K: 1.26, RANK_Q: 1.26},
}


# [V4.9.1] Hình dạng bài đối thủ lúc còn 2-3 lá (log thật ~1.100 ván Sâm HIT, thực tế / chia đều): người chơi GIỮ BỘ để về.
# Còn 2 lá: là đôi 18% (chia đều 6%); còn 3 lá: đôi+lẻ 44% (17%), sảnh 9% (3%), 3 lá lẻ 48% (79%). (tester 30/10 ván 23:06)
SAM_ENDGAME_OPP_SHAPE: Dict[int, Dict[str, float]] = {
    2: {"pair": 3.0, "other": 0.87},
    3: {"straight": 3.0, "pair": 2.6, "triple": 1.0, "other": 0.61},
}


def _opp_shape_factor(counts: Tuple[int, ...], k: int) -> float:
    tab = SAM_ENDGAME_OPP_SHAPE.get(k)
    if not tab:
        return 1.0
    mx = max(counts)
    if k == 2:
        return tab["pair"] if mx == 2 else tab["other"]
    if mx == 3:
        return tab["triple"]
    if mx == 2:
        return tab["pair"]
    m = classify_sam_cards(_concrete(counts))
    if m is not None and m.combo_type == SamComboType.STRAIGHT:
        return tab["straight"]
    return tab["other"]


SAM_MC_OVERRIDE_ABS = 0.35      # [V5.1 AI+MC] Monte Carlo hơn công thức gốc >= 0.35 lá -> ghi đè ngay
SAM_ENDGAME_EXACT_BUDGET_BIG = 4.0   # [V4.9.27] P7: đối thủ <= 3 lá mà mình >= 7 lá: cho 4 giây (1,6 giây không kịp -> bỏ bộ giải, mất 6 lá ván 16:51)
SAM_ENDGAME_FAR_MAX_OPP = 3     # [V6.8] chỉ chạy bộ giải vét cạn khi đối thủ <= 3 lá (tắt lấy mẫu nhìn xuyên bài ở 4-5 lá)
SAM_ENDGAME_FAR_MY_MAX = 10     # [V4.9.24] mình <= 10 lá (ván 12:40 tester: bỏ sảnh 5 rồi đỡ 3♣ với 10 lá, đối thủ 4 lá -> bộ giải phải chạy); tổng 2 bên vẫn <= 15
SAM_ENDGAME_FAR_WORLDS = 48     # số tay bài đối thủ lấy mẫu
SAM_ENDGAME_FAR_BUDGET = 4.0    # giây
SAM_ENDGAME_FAR_MIN_WORLDS = 12  # giải xong >= 12 tay bài mẫu là đủ dùng (hết giờ sớm hơn -> dùng nước thường)


def sam_endgame_choose(state: "SamTableState", budget_sec: float = 1.6, max_opp: int = 3,
                       opp_prior: bool = True, opp_shape: bool = True, far_max_opp: Optional[int] = None,
                       far_budget_sec: Optional[float] = None, max_worlds: Optional[int] = None) -> Optional[Tuple[SamCombo, Dict[str, float]]]:
    """[V4.8] Đối thủ (1 người) còn <= max_opp lá: liệt kê MỌI tay bài đối thủ có thể cầm (theo số lá chưa lộ, có trọng số),
    đánh tới hết ván biết hết bài cho từng tay, chọn nước có kỳ vọng tiền cao nhất. Hết giờ -> None (dùng nước thường).
    [V4.9.19] Đối thủ max_opp+1 .. far_max_opp lá và mình <= SAM_ENDGAME_FAR_MY_MAX lá: LẤY MẪU max_worlds tay bài theo trọng số."""
    if state.num_players != 2 or state.xin_sam_player is not None:
        return None
    opp_seat = 1 - state.my_seat
    k = state.cards_left[opp_seat]
    far_max_opp = SAM_ENDGAME_FAR_MAX_OPP if far_max_opp is None else far_max_opp
    far = k > max_opp
    if k <= 0 or k > max(max_opp, far_max_opp):
        return None
    if far and (len(state.my_hand) > SAM_ENDGAME_FAR_MY_MAX or len(state.my_hand) + k > 16):
        return None
    if far:
        opp_prior = opp_shape = False
        budget_sec = SAM_ENDGAME_FAR_BUDGET if far_budget_sec is None else far_budget_sec
        max_worlds = SAM_ENDGAME_FAR_WORLDS if max_worlds is None else max_worlds
    rule = ACTIVE_SAM_RULE
    unseen = _sam_unseen(state)
    uc = _rank_counts(unseen)
    worlds: List[Tuple[Tuple[int, ...], int]] = []

    def rec(r, left, cur, w):
        if left == 0:
            worlds.append((tuple(cur), w))
            return
        if r >= 13:
            return
        for take in range(0, min(left, uc[r]) + 1):
            cur[r] = take
            f = prior.get(r, 1.0) ** take if take else 1.0
            if f <= 0:
                continue
            rec(r + 1, left - take, cur, w * math.comb(uc[r], take) * f)
        cur[r] = 0

    prior = SAM_ENDGAME_OPP_PRIOR.get(k, {}) if opp_prior else {}
    rec(0, k, [0] * 13, 1)
    if not worlds:
        return None
    if opp_shape:
        worlds = [(c, w * _opp_shape_factor(c, k)) for c, w in worlds]
    pass_log = (getattr(state, "opp_pass_log", None) or {}).get(opp_seat, [])
    if pass_log:
        weighted_worlds = []
        for c, w in worlds:
            pw = float(w)
            base_cards = _concrete(c)
            for b_pass, after in pass_log:
                pw *= sam_pass_likelihood(base_cards + list(after), b_pass)
            if pw > 0:
                weighted_worlds.append((c, pw))
        if weighted_worlds:
            worlds = weighted_worlds
    if far and max_worlds and len(worlds) > max_worlds:
        # lấy mẫu theo trọng số (có lặp), gộp tay trùng
        picked = random.choices([c for c, _ in worlds], weights=[w for _, w in worlds], k=max_worlds)
        agg: Dict[Tuple[int, ...], int] = {}
        for c in picked:
            agg[c] = agg.get(c, 0) + 1
        worlds = list(agg.items())
    deadline = time.monotonic() + budget_sec
    my = _rank_counts(state.my_hand)
    board = state.board_combo if (state.board_combo is not None and not state.board_combo.is_pass) else None
    owner = None if board is None else (0 if state.board_owner == state.my_seat else 1)
    eg = _SamEndgame(rule, deadline)
    root = eg.legal(my, board, k)
    if len(root) <= 1:
        return None
    totals = {id(m): 0.0 for m in root}
    wsum = 0
    n_done = 0
    worlds.sort(key=lambda x: -x[1])
    try:
        for opp, w in worlds:
            hands = (my, opp)
            eg.memo = {}
            part = {}
            for m in root:
                if m.is_pass:
                    v = eg.solve(hands, None, None, owner)
                else:
                    v = eg.play(hands, m, board, 0)
                part[id(m)] = w * v
            for key, v in part.items():   # chỉ cộng khi giải trọn 1 tay bài (hết giờ giữa chừng không làm lệch)
                totals[key] += v
            wsum += w
            n_done += 1
    except TimeoutError:
        if far:
            if n_done < min(SAM_ENDGAME_FAR_MIN_WORLDS, len(worlds)):
                return None
        elif wsum < 0.5 * sum(w for _, w in worlds):   # [V4.9.27] P7: tay bài đã xếp theo trọng số giảm dần, giải được nửa trọng số là đủ
            return None
    vals = {id(m): totals[id(m)] / max(1, wsum) for m in root}
    top = max(vals.values())
    # bằng điểm: ưu tiên giữ nguyên phân hoạch tối ưu, BỘ nhiều lá trước (sảnh dài, sám, đôi), lá lẻ để sau; cùng loại thì bộ nhỏ trước
    near = [m for m in root if vals[id(m)] >= top - 0.05]
    _my_concrete = _concrete(my)
    _eg_sam_plan = optimal_partition_sam_hand(_my_concrete)
    _my_base_turns = _eg_sam_plan.num_turns
    _eg_sam_non2_singles = sum(
        1 for cb in _eg_sam_plan.combos
        if cb.combo_type == SamComboType.SINGLE and not cb.is_all_twos
    )
    if board is None and _my_base_turns == 2 and len(_my_concrete) == 2:
        # Cầm đúng 2 lá lẻ cuối cùng khi mở vòng (VD [9♣, 10♠] ở ván 102452 hoặc [3♣, A♥]):
        # Nếu có 1 con 2 thì mở 2 trước để về lá thường; nếu không có 2 thì bắt buộc mở lá LỚN HƠN trước!
        _non_pass_2 = [m for m in root if not m.is_pass and vals[id(m)] >= top - 0.50]
        if _non_pass_2:
            if my[RANK_2] == 1 and any(m.is_all_twos for m in _non_pass_2):
                near = [m for m in _non_pass_2 if m.is_all_twos]
            else:
                near = [max(_non_pass_2, key=lambda m: m.order_value)]
    elif board is None and _my_base_turns >= 3:
        # [V6.8 ANTI-CLAIRVOYANCE SAM ENDGAME OPEN LEAD]
        # 1) Cầm cái khi còn >= 3 nhịp: tuyệt đối không vứt Heo 2 ra bàn trống nếu có nước đánh lá/bộ thường (v >= top - 1.50)
        _non2_eg = [
            m for m in root
            if not m.is_pass and not m.is_all_twos and vals[id(m)] >= top - 1.50
        ]
        if _non2_eg:
            _best_non2_eg = max(vals[id(m)] for m in _non2_eg)
            _clean_non2_eg = [
                m for m in _non2_eg
                if vals[id(m)] >= _best_non2_eg - 0.85
                and optimal_partition_sam_hand([c for c in _my_concrete if c not in m.cards]).num_turns <= _my_base_turns - 1
            ]
            if _clean_non2_eg:
                _clean_pairs_sam_eg = [
                    m for m in _clean_non2_eg
                    if m.combo_type == SamComboType.PAIR and vals[id(m)] >= _best_non2_eg - 0.85 and vals[id(m)] > -2.0
                ]
                _clean_multis_sam_eg = [
                    m for m in _clean_non2_eg
                    if len(m.cards) >= 2 and vals[id(m)] >= _best_non2_eg - 0.50
                ]
                _low_s_cnt_eg = sum(
                    1 for cb in _eg_sam_plan.combos
                    if cb.combo_type == SamComboType.SINGLE and not cb.is_all_twos and cb.order_value < RANK_A
                )
                _a2_shield_eg = my[RANK_2] + my[RANK_A]
                # Nếu có >= 2 Đôi sạch, hoặc có Đôi sạch khi các lá lẻ thấp đã được A/2 bảo kê (như ván 195414 [Đôi 9, 7♥, A♠, 2♦]):
                # ưu tiên chạy Đôi nhỏ nhất trước!
                if len(_clean_pairs_sam_eg) >= 2 or (len(_clean_pairs_sam_eg) == 1 and _low_s_cnt_eg <= _a2_shield_eg and _a2_shield_eg >= 1):
                    near = [min(_clean_pairs_sam_eg, key=lambda m: m.order_value)]
                elif _clean_multis_sam_eg:
                    _best_m_eg = max(vals[id(m)] for m in _clean_multis_sam_eg)
                    near = [m for m in _clean_multis_sam_eg if vals[id(m)] >= _best_m_eg - 0.15]
                else:
                    _best_clean_eg = max(vals[id(m)] for m in _clean_non2_eg)
                    near = [m for m in _clean_non2_eg if vals[id(m)] >= _best_clean_eg - 0.10]
            else:
                near = [m for m in _non2_eg if vals[id(m)] >= _best_non2_eg - 0.05]
    elif board is not None:
        # Chống xé Sảnh/Đôi/Sám ra đỡ lẻ trong bộ giải cuối ván (như ván 100446)
        if board.combo_type == SamComboType.SINGLE and k >= 2:
            _no_break_def_eg = [
                m for m in root
                if m.is_pass
                or m.is_all_twos
                or optimal_partition_sam_hand([c for c in _my_concrete if c not in m.cards]).num_turns <= _my_base_turns - 1
            ]
            _valid_no_break = [m for m in _no_break_def_eg if vals[id(m)] >= top - 1.50]
            if _valid_no_break:
                _top_nb = max(vals[id(m)] for m in _valid_no_break)
                near = [m for m in _valid_no_break if vals[id(m)] >= _top_nb - 0.05]
        if (
            not board.is_all_twos
            and k <= 3
            and my[RANK_2] >= 1
            and _my_base_turns >= 3
            and (k < 4 or not any(cnt >= 4 for cnt in uc[:12]))
        ):
            _heo_margin_sam = (3.50 if _my_base_turns >= 4 else 1.50) if top < 0.0 else (1.25 if _my_base_turns >= 4 else 0.50)
            _two_eg = [
                m for m in root
                if not m.is_pass and m.is_all_twos and vals[id(m)] >= top - _heo_margin_sam
            ]
            if _two_eg:
                near = [max(_two_eg, key=lambda m: (len(m.cards), round(vals[id(m)], 2)))]
        elif (
            board.combo_type == SamComboType.SINGLE
            and my[RANK_2] == 0
            and my[RANK_A] >= 1
            and board.order_value >= RANK_8
        ):
            # Không có 2 khi đỡ lẻ cao (như ván 094535 & 100526): ưu tiên đánh A thay vì K để khóa đối thủ
            _ace_eg = [
                m for m in near
                if not m.is_pass and m.order_value == RANK_A and vals[id(m)] >= top - 0.35
            ]
            if _ace_eg:
                near = _ace_eg
    best = max(
        near,
        key=lambda m: (
            not m.is_pass,
            optimal_partition_sam_hand([c for c in _my_concrete if c not in m.cards]).num_turns <= _my_base_turns - 1
            if not m.is_pass else False,
            len(m.cards),
            -m.order_value,
        ),
    )
    # khớp về đúng lá thật trên tay (bộ giải làm trên số lượng lá theo rank)
    real = get_legal_sam_moves(list(state.my_hand), board, k)
    want = (_combo_key(best), _rank_counts(best.cards))
    match = next((m for m in real if (_combo_key(m), _rank_counts(m.cards)) == want), None)
    if match is None and not best.is_pass:
        return None
    best = match if match is not None else PASS_COMBO
    return best, {repr(m): round(vals[id(m)], 2) for m in root}
