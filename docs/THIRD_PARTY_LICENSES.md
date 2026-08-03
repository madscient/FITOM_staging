# サードパーティライセンス一覧（再配布用ステートメント）

本書は、FITOM_staging が配布するバイナリ一式（`bin/` 配下の実行ファイル・
DLL、および将来 `bin/` に追加され得る同種の成果物）に含まれる、各リポジトリ
由来のモジュールと、それらが組み込む・リンクするサードパーティソフトウェア
のライセンス関係をまとめたものです。**本リポジトリ直下の `LICENSE.txt`
（FITOM_staging 自体が管理する設定・プリセットバンク・スクリプト類への
ライセンス表示）とは別に、配布バイナリに実際に含まれるコードの権利関係を
対象とします。**

## 0. 対象モジュールと出典リポジトリ

配布物に含まれるバイナリモジュールは、以下8リポジトリの成果物です
（2026年8月時点でのビルド成果物名。将来のバージョンでファイル名が
変わる可能性があります）。

| # | 出典リポジトリ | 主な成果物 | 役割 |
|---|---|---|---|
| 1 | `FITOM_X` | `fitom_cli.exe` / `fitom_gui.exe` / `fitom_midi_*.dll` | コア本体（MIDI音源システム） |
| 2 | `FITOM_patch_editor` | `fitom_patch_editor_gui.exe` | オフラインパッチ/プロファイルエディタ |
| 3 | `FitomEmuIF` | `FitomEmuIF.dll` | FMエンジン統合 hwif プラグイン（`IHWPlugin` 実装） |
| 4 | `FitomHwIF` | `fitom_hw.dll` | 物理ハードウェア（RE1/RE4/SPFM）hwif プラグイン |
| 5 | `FitomSf2IF` | `FitomSf2IF.dll` | SF2(FluidSynth) 統合 hwif プラグイン |
| 6 | `YMEngine` | `engines/YMFMEngine.dll` | ymfm ベース FM 音源エンジン DLL（`FmEngineApi` 準拠） |
| 7 | `DSAEngine`（実体: `DSAemuEngine`） | `DSAemuEngine.dll` | digital-sound-antiques 各コアのラッパー DLL |
| 8 | `SAAEngine`（実体: `SAASoundEngine`） | `SAASoundEngine.dll` | SAASound (SAA1099) の `FmEngineApi` ラッパー DLL |

いずれも自社コード自体は **MIT License（Copyright (c) 2026 MadScient）** です。
以下、各モジュールが追加で組み込む・リンクするサードパーティコードを記載します。

---

## 1. モジュール別ライセンス詳細

### 1.1 FITOM_X（コア本体）

自社コード: MIT License。

`third_party/` 配下に git submodule として同梱し、静的にリンクするコード:

| ライブラリ | ライセンス | 著作権表示 |
|---|---|---|
| GLFW | zlib/libpng License | Copyright (c) 2002-2006 Marcus Geelnard, 2006-2019 Camilla Löwy |
| Dear ImGui | MIT License | Copyright (c) 2014-2026 Omar Cornut |
| nlohmann/json | MIT License | Copyright (c) 2013-2025 Niels Lohmann |
| RtMidi | MIT系ライセンス（改変配布時の還元条項あり） | Copyright (c) 2003-2023 Gary P. Scavone |

FitomEmuIF / FitomHwIF / FitomSf2IF は実行時にロードするプラグイン DLL
であり、FITOM_X 本体のビルド時依存には含まれません（各々 1.3〜1.5 節を参照）。

### 1.2 FITOM_patch_editor（オフラインパッチエディタ）

自社コード: MIT License。

vcpkg 経由で取得し配布バイナリにリンクする依存:

| ライブラリ | ライセンス | 備考 |
|---|---|---|
| nlohmann-json | MIT License | |
| Dear ImGui | MIT License | features: `glfw-binding`, `opengl3-binding` |
| GLFW3 | zlib/libpng License | |
| GLEW | Modified BSD License + MIT License | 本体は BSD-3-Clause、ユーティリティ部・Khronos ヘッダ定義部に MIT／Khronosライク条項が混在 |

### 1.3 FitomEmuIF（FMエンジン統合 hwif プラグイン）

自社コード: MIT License。

| ライブラリ | ライセンス | 著作権表示 / 備考 |
|---|---|---|
| RtAudio（`extern/rtaudio` submodule、静的リンク） | MIT系ライセンス（改変配布時の還元条項あり） | Copyright (c) 2001-2023 Gary P. Scavone |
| nlohmann/json | MIT License | vcpkg または FetchContent 経由 |

`YMEngine.dll`（`YMFMEngine.dll`）等の `FmEngineApi` 互換 DLL は実行時に
`LoadLibrary`/`dlopen` されるのみで、ビルド時依存はありません。

### 1.4 FitomHwIF（物理ハードウェア hwif プラグイン）

自社コード: MIT License。

| ライブラリ | ライセンス | 備考 |
|---|---|---|
| libftdi1 | **LGPL-2.1**（ライブラリ本体。付属ツール類は GPL-2.0 の場合あり） | RE1/RE4 の USB 通信。動的リンクを前提とする限り自社コードへの伝播はない |
| Boost（Asio ほか。配布物には `boost_filesystem` / `boost_log` / `boost_thread` を同梱） | **BSL-1.0**（Boost Software License 1.0） | 非コピーレフト。バイナリ配布物にライセンス全文（またはその参照）の添付が必要 |
| nlohmann/json（submodule） | MIT License | プロファイル/JSON パラメータ解析 |

> libftdi1 はさらに下位で `libusb-1.0` に依存します（配布物に `libusb-1.0.dll`
> を同梱）。libusb は LGPL-2.1 です。

### 1.5 FitomSf2IF（SF2/FluidSynth 統合 hwif プラグイン）

自社コード: MIT License。

| ライブラリ | ライセンス | リンク形態 |
|---|---|---|
| FluidSynth | **LGPL-2.1-or-later** | vcpkg 経由で**動的リンク**。`libfluidsynth-3.dll` 等として `FitomSf2IF.dll` とは別ファイルで同梱される（FitomSf2IF リポジトリの README にも明記） |
| nlohmann-json | MIT License | vcpkg 経由 |

FluidSynth 本体は無改造で動的リンクのみのため、FitomSf2IF 自体は MIT の
ままで問題ありませんが、**再配布時は `libfluidsynth-3.dll` 自体に対して
LGPL-2.1-or-later の条件（ライセンス表示・差し替え可能性の確保等）を
別途遵守する必要があります**。

なお、SF2 サウンドフォント（`.sf2`）ファイル自体を配布物に同梱する場合、
音色データごとに個別のライセンスが存在するため別途確認が必要です
（本リポジトリの現行配布物には `.sf2` ファイルは同梱されていません）。

### 1.6 YMEngine（`YMFMEngine.dll`）

自社コード: MIT License。

| ライブラリ | ライセンス | 著作権表示 |
|---|---|---|
| ymfm（`extern/ymfm` submodule、静的リンク） | **BSD 3-Clause License** | Copyright (c) 2021, Aaron Giles |

### 1.7 DSAEngine（実体: `DSAemuEngine.dll`）

自社コード: MIT License（`DSAemuEngine.cpp`）。

digital-sound-antiques 製の各チップエミュレーションコアを git submodule
として静的リンク。**全て MIT License**（Copyright (c) Mitsutaka Okazaki）:

| submodule | 対象チップ |
|---|---|
| emu2149 | YM2149 / AY-3-8910 (SSG) |
| emu2413 | YM2413 (OPLL / OPLLP / OPLLX / VRC7) |
| emu8950 | Y8950 / YM3526 (OPL) / YM3812 (OPL2) |
| emu2212 | Konami SCC |
| emu76489 | SN76489 (DCSG) |

### 1.8 SAAEngine（実体: `SAASoundEngine.dll`）

自社コード: MIT License（`SAASoundEngine.cpp`）。

| ライブラリ | ライセンス | 著作権表示 |
|---|---|---|
| SAASound（`extern/SAASound` submodule、静的リンク） | **BSD 3-Clause License** | Copyright (c) 1998-2004, Dave Hooper。Copyright (c) 2004-2025, Dave Hooper + Simon Owen |

[stripwax/SAASound](https://github.com/stripwax/SAASound) は
`SAASoundEngine/extern/SAASound/LICENCE` の内容を直接確認したところ
**BSD 3-Clause License** でした（YMEngine 側の `README_ymfm.md` に
「SAASound: GPL-2.0」という記載がありましたが、これは誤りです。
1.6 節の記述もあわせて訂正済み）。

BSD 3-Clause は MIT と互換性のある非コピーレフトライセンスのため、
`SAAAmp.cpp` / `SAADevice.cpp` / `SAAEnv.cpp` / `SAAFreq.cpp` /
`SAAImpl.cpp` / `SAANoise.cpp` / `SAASndC.cpp` / `SAASound.cpp` /
`SAAConfig.cpp` / `minIni.c` 等を `SAASoundEngine.cpp` と共に静的
コンパイルして単一の `SAASoundEngine.dll` に統合する現行の構成でも
法的な問題はありません。ただし、**バイナリ（DLL）形態で再配布する場合は
BSD 3-Clause の条件②により、上記の著作権表示とライセンス全文を
同梱ドキュメントに記載する必要があります**（4.4節に全文を掲載）。
また「Dave Hooper」の名称を宣伝・推奨目的に使用しないこと（条件③）
にも留意してください。

---

## 2. ライセンス別の注意点まとめ

| ライセンス | 該当モジュール | 再配布時の主な義務 |
|---|---|---|
| MIT / zlib-libpng / BSD-3-Clause | 大半の自社コードおよび GLFW・Dear ImGui・nlohmann/json・RtMidi・RtAudio・ymfm・emu2149系・GLEW・SAASound（SAAEngine） 等 | 著作権表示とライセンス全文の同梱（非コピーレフト、ソース開示義務なし） |
| BSL-1.0（Boost） | FitomHwIF が同梱する boost_filesystem / boost_log / boost_thread | ライセンス全文（または参照）の同梱。ソース開示義務なし |
| LGPL-2.1 系 | libftdi1 / libusb-1.0（FitomHwIF）、FluidSynth（FitomSf2IF） | 動的リンクであれば自社コードの非公開配布は可能。ライブラリ自体の著作権表示・ライセンス文の添付、差し替え可能性の確保が必要 |

> GPL 系コンポーネントは現時点で本ステートメントの対象8モジュールには
> 含まれていません。

---

## 3. 対象範囲外の関連事項（参考）

本書は上記8リポジトリが生成する**バイナリモジュール**を対象としています。
`FITOM_staging` 本体が保持する `banks/` 配下の音色プリセットデータ
（JSON 形式、コードではない）には、DX27/DX100・FB-01・TX81Z 等の商用
ハードウェアのファクトリープリセット変換データ、N88-BASIC OPNA ドライバ
プリセット、ALSA sbiload 標準音色、MA-2 VMA 変換データなどが含まれており、
これらは本書の対象外です。データ自体の再配布可否は別途出典ごとに確認が
必要な場合があります。

---

## 4. ライセンス全文

### 4.1 MIT License（本リポジトリ関連コードで共通の書式）

```
MIT License

Copyright (c) <year> <copyright holder>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

適用対象と `<year> <copyright holder>`:

- FITOM_X / FITOM_patch_editor / FitomEmuIF / FitomHwIF / FitomSf2IF /
  YMEngine / DSAEngine / SAAEngine（自社コード全て）:
  `2026 MadScient`
- Dear ImGui: `2014-2026 Omar Cornut`
- nlohmann/json: `2013-2025 Niels Lohmann`
- emu2149 / emu8950 / emu2212 / emu76489: `2014 Mitsutaka Okazaki`
- emu2413: `2001-2019 Mitsutaka Okazaki`
- GLEW（ユーティリティ部）: 上流 LICENSE.txt 参照

RtMidi / RtAudio は上記 MIT 文言に加え、以下の付帯条項（拘束力のない
努力義務）を含みます:

```
Any person wishing to distribute modifications to the Software is
asked to send the modifications to the original developer so that
they can be incorporated into the canonical version.  This is,
however, not a binding provision of this license.
```

### 4.2 zlib/libpng License（GLFW / GLFW3）

```
Copyright (c) 2002-2006 Marcus Geelnard
Copyright (c) 2006-2019 Camilla Löwy

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would
   be appreciated but is not required.

2. Altered source versions must be plainly marked as such, and must not
   be misrepresented as being the original software.

3. This notice may not be removed or altered from any source
   distribution.
```

### 4.3 BSD 3-Clause License（ymfm）

```
BSD 3-Clause License

Copyright (c) 2021, Aaron Giles
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

GLEW 本体（Modified BSD License）もほぼ同一書式です（上流 `LICENSE.txt`
参照）。

### 4.4 BSD 3-Clause License（SAASound）

`SAASoundEngine/extern/SAASound/LICENCE` より一次確認済みの全文:

```
SAASound - a portable Phillips SAA 1099 sound chip emulator
-----------------------------------------------------------

Copyright (c) 1998-2004, Dave Hooper <dave@beermex.com>
Copyright (c) 2004-2025, Dave Hooper <dave@beermex.com> + Simon Owen <simon@simonowen.com>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

- Neither the name Dave Hooper nor the names of its contributors may
  be used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

「Dave Hooper」の名称を、貢献者表示以外の宣伝・推奨目的に使用しないこと
（条件③）に留意してください。

### 4.5 長文ライセンス（全文は上流を参照）

以下は条文が長いため全文の転記を省略します。再配布パッケージ作成時は
各公式サイトから最新の全文を取得し、対応する DLL と共に同梱してください。

- **BSL-1.0**（Boost Software License 1.0）: <https://www.boost.org/LICENSE_1_0.txt>
- **LGPL-2.1**: <https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>
  （libftdi1・libusb-1.0・FluidSynth に適用）

---

*本書は各出典リポジトリの `LICENSE` / `README.md` / 実際の submodule
内 `LICENCE` の一次確認に基づき作成した時点のスナップショットです。
依存関係やライセンス表記は各リポジトリ側で変更され得るため、実際の
配布物を作成する際は最新のソースを再確認してください。*
