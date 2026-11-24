# 職場から家へ：論文 11（下書き 3）と psf-os 0.3.3 の読み（2026-11-24）

職場クロードが書いた。作成は 2026-11-24 00:37 CET（`TZ=Europe/Zurich date` の出力）。tex とコードは変えていない（案だけ）。GitHub と IBM には触れていない。psf-os はバンドルから clone しただけ。

**まとめ：** 数の誤りは見つからなかった。直したほうがよいのは次の 5 か所。

- 要旨と結論の言い過ぎ 2 か所（「+0.03〜+0.10」、FLAT を「回ごと」と言い切る文）
- 晩をまたいだ比べ 1 か所
- 記号 M の二重の意味
- 0.3.3 の「バイトまで同じ」の範囲の書き方（CHANGELOG・README・論文の 3 か所）

コードの重い誤りはなかった。小さい不具合 1 つ（`.devN` の順）と、説明の食い違い 3 つ。

---

## 1. 論文 11

### 1a. 直したほうがよい（中身）

| 行 | 今の文 | 問題 | 案 |
|---|---|---|---|
| 288 | Where a qubit waits changed what a dynamic circuit kept by $+0.03$ to $+0.10$ in these tests. | 本文には +0.014（P0、M − F）と +0.025（P0、MP）の KEEPS MORE がある。SAME（fence −0.004、n = 7・8、P3）もある。下限 +0.03 は言い過ぎ | Where a qubit waits changed what a dynamic circuit kept by up to $+0.10$ in these tests ($+0.014$ to $+0.097$ where it read KEEPS MORE; SAME WITHIN ERROR on some chains and at $n = 7, 8$). |
| 199–200 | the loss per added bit is per round, not per conditional, although the conditionals grow from 9 to 20. | FLAT は「この撃ちの数では加速が見えない」まで。しかも 205 行で、別の晩（fez、n = 6〜8）では落ちが増えている。読者には矛盾に見える | read FLAT: on this night the loss per added bit did not grow with the conditionals (from 9 to 20) beyond 2 SE (about 0.008 on the log share). 205 行のあとにも 1 文を足す：On another device and night, from $n = 6$ to 8, it grew; the two ranges are read on their own. |
| 206 | The fez night read 0.4236 against the extrapolated 0.72 declared from the marrakesh night (another device and calibration). | 92 行の「違う晩の値は並べるだけで、比べない」に、"against" がかかって見える | The declared expectation, extrapolated from the marrakesh night, was 0.72; the fez night read 0.4236 (another device and calibration; set beside, not compared). |
| 137 と 192 | (M) = たぶん \|1⟩ を置く形 / "added M on L = 3" = 1 回多く試す段 | 同じ M が別の意味で 2 回出てくる。初めての読者は混同する | 駐車の形を M（parked likely）から別の文字に変える（例：K）。または 192 行を "added one more try (M)" にして、方法の節で段 M を定義する |
| 235–236 | Rebuilt with 0.3.3, the recorded builds of 2026-11-21 and 22 were the same files byte for byte | 記録と比べたのは試験回路（ゲートとバイト）。「全ファイル同じ」は 0.3.2 と 0.3.3rc1 の組み直しどうしの比べ。manifest には `compiled` が足され、時刻も違う（`notes/checks_2026-11-23/README.md`） | Rebuilt with 0.3.3, the test circuits of the six recorded nights of 2026-11-21 and 22 were the same as recorded, gate for gate and byte for byte, and every wait of a qubit psf-os parked (2214) stayed parked in the circuit as sent. |
| 44、218 | Removing every phase conditional changed the share by … / removing every phase conditional with its real wait changed … | S は条件を外しただけでなく、正しい補正を無条件で置いている。"with its real wait" は読み取りにくい | 44：Replacing every phase conditional by its right correction, unconditional, changed the share by $+0.005$ (2 SE 0.006). 218：Beside, S $-$ F (the phase conditionals replaced by their right corrections, with the measurement waits kept) changed the share by … |
| 160 | F6 decodes during the wait and cannot protect a memory | F6 は読み出しの前に符号を解いて、d0 だけで待つ。「待ちの間に解く」は不正確 | F6 undoes the code before the syndrome is read, so that one qubit waits; it cannot protect a memory and is not error correction. |
| 262 | no mismatch over 65 nights | 家の VS の相談書には「引数なしで流すと、52 夜を数えました」とある。数え方の違いなら、どちらかに揃える | 出す前に `tools/check_readme_numbers.py` の出力の夜の数を確かめて書く |
| 103 | the device rule excluded ibm\_marrakesh, to test the rules on other devices | 宣言（rus_fence）は「オーナーの選択：off marrakesh」。引き継ぎ書には「残り 60 分を切った・待ちが短い方」とある。理由の書き方は家で確かめてほしい | 理由が「ほかの装置で読む」で正しければ、このままでよい |

### 1b. 分かりにくい所（初めての読者）

- **定義のない言葉：**
  - "share"（初出は 112 行。正しい答えの撃ちの割合）
  - 鎖の名前 NF・P0・P2・P3 と処方 P1・P2+M（138 行・190 行。論文 10 の言葉）
  - "ring sentinel"（101 行）
  - "off and floor arms"（253 行）
  - 案：方法の Words の段に 2〜3 行足す。例："share: the fraction of shots with every bit right"、"NF, P0, P2, P3: the four RUS prescriptions of paper 10 (…)"、"M: one more try"。
- **要旨の 32 行** "Over nine declared runs (eleven tests) in eight device sessions"：runs・tests・sessions の違いが初読では分からない。
  - 案：Nine declared runs (eleven tests; the decoy and loopvar tests shared one job) were sent in eight charged sessions on three devices.
- **173–174 行** "the declared prediction was the control's repeat (D0)"：読みにくい。
  - 案：The one declared prediction, that the control (D0) repeats paper 10's loss, held.
- **169 行**：論文 10 の「損はレジスタのビットの順に従った」と、decoy の答え「最初の条件付き項目が損をする」の関係を 1 文で示すと流れがよい。
  - 案："…, and that the item whose bits came first lost. A decoy test asked whether that is the register's first bits or the first conditional item:"
- **227–228 行** "a night replayed with a ledger line of the same calibration starts from the ledger's prescriptions and stops where a circuit is not in one recorded job"：何のための機能かが分からない。
  - 案：A recorded night can be replayed from its raw counts: with a ledger line of the same calibration it starts from the ledger's prescriptions, and it stops at the first circuit that no recorded job holds. 論文の主張に要らなければ削ってよい。
- **253 行** "The off and floor arms were not sent on 2026-11-21"：どの試験か書く（qpe-parked か weekend か）。

### 1c. 英語

| 行 | 今 | 案 |
|---|---|---|
| 290 | Neither cost CZ or changed the noiseless answer | Neither cost CZ nor changed the noiseless answer |
| 239 | The branch-cost split failed by a placeholder | The branch-cost split failed because of a placeholder |
| 41 | cost the first one 0.057 | cost the first of them 0.057 |
| 56 | held the likely value 1 as $\ket{0}$ | held the likely value 1 in $\ket{0}$ |
| 173 | whatever stands before it; the declared prediction was … | 上の 1b の案 |

ほかに目立つ誤りはない。

### 1d. 直す必要がないと思う所

- 要旨と本文の数は、次のものが一致していた：706 s、11 予言、+0.039 / −0.004、+0.031〜+0.039、+0.029 / +0.052、+0.097 / +0.025、+0.015 / +0.022、+0.028 / +0.011、0.929、0.057 / 0.085、p 0.006、0.424 / 0.201。
- 表の課金と予言の数も、OUTLINE と合っていた。
- 計算し直して、丸めの範囲で合っていたもの：ln の落ち（0.0274、0.0308、0.1266、0.1851）、天井からの差（+0.425 / +0.492 / +0.539）、112 / 59.6 = 1.9 倍、χ² 7.11（9 自由度）の p（丸めた 7.11 からは 0.626。記録の 0.625 は丸める前の χ² からと思われる）。
- 先行研究の段の言い方（"not exhaustive, we did not find"）は控えめで適切。
- 参考文献は、TimeStitch（ACM TQC 4(1)）、Córcoles（PRL 127, 100501）、Cao（arXiv:1711.11240）を確かめた。Liu 2026 と Zhong 2025 は、職場では確かめられない（ウェブにつながない）。
- 限界の節と、うまくいかなかったことの節は十分。

---

## 2. psf-os 0.3.3（release-0.3.3、a45c54a）

### 2a. 説明とコードの食い違い（直したほうがよい）

1. **「0.3.2 が組むものはすべて、0.3.3 もバイトまで同じに組む」の範囲**
   - 該当箇所：CHANGELOG 0.3.3 の 6〜8 行、README 148 行 "Every circuit 0.3.2 builds is built byte for byte the same."
   - 範囲が広すぎる理由は 3 つ。
     - (i) manifest には `compiled` が必ず足される（README 自身の 141 行）。
     - (ii) 装置の記録に時間の制約があると、格子から外れた遅延を 0.3.3 は拒む（0.3.2 は組んだ）。
     - (iii) 駐車がコンパイルで崩れたビルドも、0.3.3 は拒む。
   - 「every file the same」も、manifest については不正確。checks の README では「時刻・環境・psf_os_build・新しい compiled を除けば同じ」と書いてある。
   - 案（CHANGELOG）：On the six recorded nights of 2026-11-21 and 22 (device records without timing constraints), 0.3.2 and 0.3.3rc1 built the same files byte for byte — run records, QPY, circuits.qpy, build.json, checks.json — and the same manifests but for the new `compiled` key, the time and the build environment. With timing constraints in the device record, a delay off the grid is refused; a build whose parking the compiler did not keep is refused.
   - README 148 行も同じ趣旨に短くする。
2. **"Recorded beside the job"**（README 141 行、CHANGELOG 8 行 "recorded beside the job"）
   - 実際は `job/manifest.json` の中（`manifest["compiled"]`）。ジョブの外の `checks.json` とは別物。
   - 案：Recorded in the job's manifest (`manifest["compiled"]`).
3. **遅延の格子**
   - CHANGELOG の "or is shorter than min_length, is refused" に対して、コード（`job.delay_grid_problems`）は「0 でない長さで min_length より短いもの」を拒む。長さ 0 は通る。
   - 案：or is shorter than min_length (a zero length aside)
4. **PEP 440 の順**（`feedforward.version_key`。不具合、影響は小さい）
   - pre のない `.devN`（例 `0.3.0.dev1`）が、`0.3.0rc1` の後ろ（rc と final の間）に並ぶ。PEP 440 では `0.3.0.dev1 < 0.3.0a1`。
   - `packaging.version.Version` で並べた順と一致しなかった（`0.3.0rc1.dev2` は正しく rc1 の前に来る）。
   - 安全の判定（`parks_by_default` など）は、final より前と正しく出るので、今の使い方に害はない。
   - `.postN` は `None`（「駐車しない版」の扱い）になる。
   - 案：pre がないときの dev の鍵を、a より前にする（例：`_PRE` を −1 にする）。`.postN` は受け付けないことを docstring に書く。CHANGELOG の "PEP 440's order" は、直すまで「rcN・aN・bN と final の順」に狭める。

### 2b. 確かめて、食い違いがなかった所

- **コンパイル後の駐車の確かめ**（`compiled.check_parked`）
  - always は P(\|1⟩) ≤ 1e-9、likely は < 0.5。待ちの最初から最後のアンカーの直後まで調べる。
  - build、build_bundle、build_pack_fixed の 3 つで呼ばれる。
  - 駐車がないと計算しない。駐車は足跡の上限の中でしか起きないので、大きな回路で止まらない。
- **待ち・柵の深さ・回路の要約の記録**：`waits_record`（物理量子ビット、P(\|1⟩) を 4 桁、entangled）、`fences`（depth の前と後。時間の記録があれば dt と µs も）、`summary`（CZ、depth、gatehash）。`loop.summary_line` もある。
- **命令の長さと時間の刻み**：`device.timing_of` が読むのは `props.duration` だけ（x、sx、cz、measure、reset）。error は読まない。`from_target` は変わっていない。
- **輪の既定**
  - `start(paired=None)` は装置では paired。装置で paired=False なら、cross_job=True がないと拒む。空回しは今までどおり。
  - `same_job` は、記録の manifest にない `compiled` を外して比べる。
- **遅延の上限 100 µs と課金**
  - `DELAY_LIMIT_US` = 100。1 回路で、1 量子ビットあたりの遅延の合計の最大を見る。
  - assemble が拒み、build・bundle・pack_fixed から `allow_long_delay` が渡る。
  - `qpu_seconds` = … + shots × Σ回路の遅延。
  - 遅延の記録と dt への変換は上の階層だけを見る。ただし条件の中の遅延は入口（`_check_block`）で拒まれるので、漏れはない。
- **候補の版名 `X.Y.ZrcN`**
  - `same_version` は rc まで区別する。
  - `parks_by_default('0.3.0rc1')` は False、`parks_by_default('0.3.0')` は True、`parks_likely_by_default('0.3.1rc1')` は False。
- **版の文字**：pyproject 0.3.3、`__version__` 0.3.3。CHANGELOG の「tests/test_checks_durations.py (12)」は 12 件で一致。

### 2c. 小さい提案（直さなくてもよい）

- README の Tests の節の「0.1.0: 286 passed, 1 skipped」は古い。0.3.3 の数（下の 2d）に替えるとよい。
- "slow" の印は 9 か所に付いている。parametrize で、README の「23 tests」になるのかもしれない。出す前に `pytest -m slow --collect-only -q` の数で確かめるとよい。

- 職場の qiskit-ibm-runtime 0.51.0 では、`psf_os/ibm.py` の `SamplerV2` に非推奨の警告が出た（0.50.0 から非推奨。3 か月以上たてば消える）。家の 0.49 ではまだ出ない。今すぐ直す必要はないが、次の版で見ておくとよい。

### 2d. テスト

- 職場で `TOQB_DIR` なしで流した。release-0.3.3、Python 3.13、qiskit 2.6.1、qiskit-aer 0.18.2。
- 結果：**385 passed、30 skipped、失敗 0**（合わせて 415 で予定どおり、14 分 7 秒）。
- 30 の skip は、研究ノートを読むテストと、重い tensor-network のテスト。

---

## 3. 家の VS の改良案（相談）についての職場の意見

オーナーと決める前の材料として書く。

- **すぐ作ってよい**（宣言の決まりを変えない、道具の直し）
  - `check_readme_numbers.py`：0 夜しか確かめなかったときはエラーにする。
  - 書き方の lint：「nothing」「at most」「only」、2 SE のない脇の値を拾う。最初は警告だけにする。
  - 答えの sha256 を README か scores.json にも書く。
  - 番兵の無雑音の結果を記録に書く。
- **価値が大きい**：別系統の採点の一般化。
  - 送った回路の measure 命令から対応を読む 2 本目の採点を、研究ノートの tools に置く（`ow_independent_check` を一般化する）。
  - build.json を信じている点（VS の案 4）も、これで同時に塞がる。
  - これからの晩から使えばよく、過去の晩は今の reproduce のままでよい。
- **宣言の決まりに関わる**（オーナーの判断）
  - **偏りの欄**（装置 − 答え、2 SE つき）：まず脇の値の決まった欄にするのに賛成。判定に入れるのは、2〜3 晩分の値を見てからでよい。
  - **双子の「意味のある差の大きさ」**：δ を宣言で決める案の前に、いつでも出せる「この試験が見分けられる最小の差（2 SE）」を脇の値の決まった欄にする案を勧める。そうすれば、検出力の低い SAME（VS の 5）も読み手に見える。δ を判定に入れるのは、そのあとでよい。
- **次の試験の案**
  - 窓の量子ビットごとの Z の L と F の対の比べ（VS の 2）は、11-23 の生の数から机の上で出せる。IBM の残り約 50 分を使う前に、まず脇の読みとして出すのがよい。
  - 光円錐の回路を複数並べる案（VS の 1）は、場所の違いを測る対照が要る。残り時間の使い道としては、オーナーの判断。
