/**
 * Preflight Multi-Language Translation Engine
 * Authentic baseball terminology for English, Japanese (NPB), Korean (KBO), Spanish (LMB/Winter), and Traditional Chinese (CPBL).
 */

const PREFLIGHT_TRANSLATIONS = {
  en: {
    lang_toolbar_label: "Language / 言語 / 언어 / Idioma / 語言:",
    brand_title: "Preflight",
    brand_sub: "Computer Vision · Multi-League Showcase",
    nav_overview: "Overview",
    nav_coverage: "Coverage Board",
    nav_leads: "Ranked Leads",
    nav_pricing: "Pricing & Access",
    nav_arch: "Architecture & CV",
    nav_request_pilot: "Request Pilot Access",

    hero_eyebrow: "Public Showcase · MLB, NCAA, NPB, KBO, CPBL & LMB Advance Scouting Intel",
    hero_h1: 'Computer Vision "Spot the Difference" Engine for Pitch Tipping & Mechanical Variance.',
    hero_desc: "Preflight automates high-resolution landmark and bounding-box tracking across global leagues to detect pitch-to-pitch mechanical variation—glove set height, forearm exposure, torso posture, hand depth, and catcher target positioning—strictly before ball release.",
    hero_cov_curr_lbl: "Current Completed Coverage:",
    hero_cov_curr_val: "100% of all NL West pitching staffs & rotation arms completed and modeled.",
    hero_cov_cap_lbl: "Full Pipeline Capabilities:",
    hero_cov_cap_val: "Full-scale pipeline capabilities to track and model your entire respective league—MLB (all 30 clubs), NCAA Division I College Baseball, NPB (Japan), KBO (Korea), CPBL (Taiwan), Mexico (LMB), and Winter Leagues directly from Synergy, TrackMan, or stadium video feeds.",
    hero_btn_roupp: "Explore Showcase: Landen Roupp →",
    hero_btn_erod: "Eduardo Rodriguez →",
    hero_btn_webb: "Logan Webb →",
    hero_btn_burns: "NCAA: Chase Burns →",
    hero_btn_sasaki: "NPB: Roki Sasaki 🇯🇵 →",
    hero_btn_choi: "KBO: Won-tae Choi 🇰🇷 →",
    hero_btn_gulin: "CPBL: Gu Lin Ruei-Yang 🇹🇼 →",
    hero_btn_rios: "LMB: Wilmer Ríos 🇲🇽 →",
    hero_btn_schedule_audit: "Request Pilot / Schedule Scouting Audit →",

    meta_domain_label: "Domain",
    meta_domain_val: "Computer Vision Multi-League Showcase",
    meta_coverage_label: "Completed Coverage",
    meta_coverage_val: "100% NL West Staffs Modeled",
    meta_capabilities_label: "Pipeline Scope",
    meta_capabilities_val: "MLB (30 Clubs), NCAA, NPB, KBO, CPBL, LMB",
    meta_pitchers_label: "Showcase Pitchers",
    meta_pitchers_val: "Roupp (MLB), Burns (NCAA), Sasaki (NPB), Choi (KBO), Gu Lin (CPBL), Ríos (LMB)",
    meta_catcher_label: "Showcase Catcher",
    meta_catcher_val: "Gabriel Moreno (ARI) Battery",
    meta_feed_label: "Baseline Feed",
    meta_feed_val: "Broadcast Center-Field (CF) & Synergy 1080p60 Ingest",
    meta_scope_label: "Detection Scope",
    meta_scope_val: "Glove, Posture, Forearm, Set Timing, Catcher Setup",
    meta_window_label: "Actionable Window",
    meta_window_val: "Set Position → Hand Break (0s Leakage)",

    filter_all_leagues: "All Leagues (9 Showcase Profiles)",
    filter_all_orgs: "All Organizations (12)",
    filter_nlwest: "NL West Focus (5 Clubs)",
    filter_mlb: "MLB 🇺🇸 (NL West)",
    filter_ncaa: "NCAA 🎓 (College D1)",
    filter_npb: "NPB 🇯🇵 (Japan)",
    filter_kbo: "KBO 🇰🇷 (Korea)",
    filter_cpbl: "CPBL 🇹🇼 (Taiwan)",
    filter_lmb: "LMB 🇲🇽 (Mexico)",

    workflow_eyebrow: "The 4-Step Operational Pathway",
    workflow_h2: "From Automated Computer Vision to Batter's Box Execution",
    workflow_lede: "How collegiate programs and professional franchises turn computer vision variance detection into real on-field wins.",
    step1_num: "STEP 01",
    step1_title: "Model Finds the Pattern",
    step1_desc: "Preflight automatically ingests Synergy feeds and game video, tracking 30+ biomechanical landmarks to isolate physical variance between pitch types.",
    step2_num: "STEP 02",
    step2_title: "Analysts Confirm the Tell",
    step2_desc: "Advance scouts and quants vet raw variance against pitch-mix baselines, permutation nulls, and multi-game holdout validation to eliminate random noise.",
    step3_num: "STEP 03",
    step3_title: "Coaches Teach Recognition",
    step3_desc: "Hitting coaches package validated mechanical tells into clear visual cues (glove elevation, leg lift tempo, catcher target height) and count-specific plans.",
    step4_num: "STEP 04",
    step4_title: "Players Execute on Field",
    step4_desc: "Hitters in the box and baserunners on second base recognize the tell before arm acceleration, eliminating secondary pitch types in target counts.",

    catcher_eyebrow: "Real Battery Advance Scouting Intel",
    catcher_h2: "Catcher Pre-Pitch Setup & Target Placement Tells",
    catcher_lede: "Tipping isn't just the pitcher. Preflight tracks catcher stance width, target elevation, and stillness timing before delivery initiation.",
    catcher_moreno_title: "Gabriel Moreno (ARI Diamondbacks · Catcher)",
    catcher_moreno_sub: "Pre-Pitch Glove Target Elevation & Crouch Stillness Timing (NL West Battery Analysis)",
    catcher_stat1_lbl: "Signal Floor Separation",
    catcher_stat2_lbl: "Glove Target Shift",
    catcher_stat3_lbl: "Discrimination Rate",
    catcher_stat4_lbl: "Temporal Leakage",
    catcher_cue1_title: "1. Pre-Pitch Glove Target Height Shift (Fastball vs. Changeup/Slider):",
    catcher_cue1_desc: "On 4-Seam Fastballs, Moreno sets his target glove 3.4 inches higher at settle. On Changeups and Sliders, he drops into a deeper crouch and pre-sets low.",
    catcher_cue2_title: "2. Stance Stillness Timing Prior to Leg Lift Initiation:",
    catcher_cue2_desc: "On offspeed selections, Moreno achieves full glove stillness 210ms earlier than on fastballs, giving runners on second base and dugout coaches a clean pre-pitch advance tell.",
    catcher_cta_more: "Request Full Opponent Catcher Scouting Audit →",

    showcase_eyebrow: "Global League Showcase Dossiers",
    showcase_h2: "Unlocked Benchmark Mechanical Variance Leads (NCAA, NPB, KBO, CPBL, LMB, MLB)",
    showcase_lede: "Examine top physical discrepancy leads, broadcast video sources, and holdout-validated biomechanical metrics across professional and collegiate leagues.",
    
    showcase_card_roupp_title: "Landen Roupp · SF Giants (MLB 🇺🇸)",
    showcase_card_roupp_badge: "MLB SHOWCASE",
    showcase_card_roupp_desc: "Curveball (CU) vs Sinker (SI) & Changeup (CH). Peak leg lift glove elevation (+0.06 torso lengths covering jersey letters on CU at -0.28s before hand break) and hand burial depth in pocket at set (-0.85s).",
    showcase_card_roupp_btn: "View Mechanical Breakdown →",

    showcase_card_erod_title: "Eduardo Rodriguez · ARI D-backs (MLB 🇺🇸)",
    showcase_card_erod_badge: "MLB SHOWCASE",
    showcase_card_erod_desc: "Changeup (CH) vs Cutter (FC) & Fastball (FF). Initial knee rise acceleration tempo (+22% faster knee ascent on CH at -0.50s) and sub-belt glove set height on FC.",
    showcase_card_erod_btn: "View Mechanical Breakdown →",

    showcase_card_webb_title: "Logan Webb · SF Giants (MLB 🇺🇸)",
    showcase_card_webb_badge: "MLB SHOWCASE",
    showcase_card_webb_desc: "Changeup (CH) vs Sinker (SI) & Sweeper (SL). Glove acceleration into leg lift (+18% faster upward snap at -0.45s) and 15° outward glove cant on Sweeper.",
    showcase_card_webb_btn: "View Mechanical Breakdown →",

    showcase_card_burns_title: "Chase Burns · Wake Forest (NCAA 🎓)",
    showcase_card_burns_badge: "NCAA SHOWCASE",
    showcase_card_burns_desc: "4-Seam Fastball (FF 101mph) vs Slider (SL 89mph). Glove set presentation height (+3.2 in higher set at sternum on FF at -0.80s, 88.4% signal floor, d=1.18) in Synergy CF.",
    showcase_card_burns_btn: "View NCAA Breakdown →",

    showcase_card_sasaki_title: "Roki Sasaki · Chiba Lotte (NPB 🇯🇵)",
    showcase_card_sasaki_badge: "NPB SHOWCASE",
    showcase_card_sasaki_desc: "Splitter/Forkball (FS 92mph) vs 4-Seam Fastball (FF 102mph). Set stillness dwell (+180ms longer pause on splitter wedge at -0.85s, 91.2% signal floor, d=1.42) on Pacific League TV 60fps.",
    showcase_card_sasaki_btn: "View NPB Breakdown →",

    showcase_card_choi_title: "Won-tae Choi · LG Twins (KBO 🇰🇷)",
    showcase_card_choi_badge: "KBO SHOWCASE",
    showcase_card_choi_desc: "Changeup (CH) vs Sinker (SI). Right wrist crease burial depth (+2.4 in deeper inside pocket at -0.80s, 87.8% signal floor, d=1.26) via SPOTV CF ingest.",
    showcase_card_choi_btn: "View KBO Breakdown →",

    showcase_card_gulin_title: "Gu Lin Ruei-Yang · Uni-Lions (CPBL 🇹🇼)",
    showcase_card_gulin_badge: "CPBL SHOWCASE",
    showcase_card_gulin_desc: "4-Seam Fastball (FF 156km/h) vs Forkball (FS 136km/h) & Curveball (CU). Chin-level glove elevation at peak knee apex (-0.32s, 89.5% signal floor, d=1.34) on CPBL TV 60fps.",
    showcase_card_gulin_btn: "View CPBL Breakdown →",

    showcase_card_rios_title: "Wilmer Ríos · Acereros de Monclova (LMB 🇲🇽)",
    showcase_card_rios_badge: "LMB SHOWCASE",
    showcase_card_rios_desc: "Changeup (CH) vs Sinker (SI). Right forearm outward abduction flare (+14° angle creating daylight through elbow at -0.80s, 88.6% signal floor, d=1.30) on LMB TV.",
    showcase_card_rios_btn: "View LMB Breakdown →",

    roster_eyebrow: "Full Multi-League & Collegiate Coverage",
    roster_h2: "35+ Audited Arms & Full Rotation Pre-Series Database",
    roster_lede: "Complete division rotations, bullpens, and conference opponent audits available under Enterprise & Collegiate Pilots.",

    lock_banner_title: "🔒 Enterprise Scouting Database Lock",
    lock_banner_desc: "Access full 60+ arm MLB, NPB, KBO, CPBL, Mexico, Winter Leagues, and NCAA Division I team dossiers.",
    lock_banner_btn: "Request Enterprise Pilot Access →",

    modal_badge: "🔒 Confidential Scouting Pilot Request",
    modal_title: "Request Preflight Scouting Pilot & Access",
    modal_desc: "Inquire about 2027 College Licensing (k–k range), Conference Lockout Exclusivity (k–k range), or Pro Enterprise Deployments. A signed mutual NDA is executed prior to video sharing.",
    modal_lbl_name: "Full Name *",
    modal_lbl_org: "Organization / School *",
    modal_lbl_email: "Work / Official Email *",
    modal_lbl_level: "Level / Division *",
    modal_lbl_tier: "Tier of Interest *",
    modal_lbl_notes: "Notes / Specific Opponents / Timeline",
    modal_submit: "Submit Pilot Request →",
    modal_direct_email: "Direct Email",
    modal_success_title: "Thank you for your pilot request.",
    modal_success_body: "Your default email client has been prepared with your request parameters directed to Colby Morris (colby.morris08@gmail.com). We will respond promptly to coordinate NDA execution and video setup.",

    footer_text: "Preflight Computer Vision · Proof of Concept to Live Rollout · Built by Colby Morris"
  },

  ja: {
    lang_toolbar_label: "言語 / Language:",
    brand_title: "Preflight",
    brand_sub: "コンピュータービジョン · 国際リーグ版ショーケース",
    nav_overview: "概要",
    nav_coverage: "球団カバレッジ",
    nav_leads: "動作差ランキング",
    nav_pricing: "料金プラン・独占権",
    nav_arch: "解析技術・CV",
    nav_request_pilot: "パイロット申請",

    hero_eyebrow: "公開ショーケース · NPB (日本), MLB, NCAA (大学), KBO (韓国), CPBL (台湾), LMB (メキシコ) 高度スカウティング",
    hero_h1: "ピッチティッピング（投球癖）＆ キャッチャー構え検知 コンピュータービジョンAI",
    hero_desc: "Preflightは世界各国のプロ・大学リーグ映像から高精度な骨格ランドマークと検出ボックスを自動追跡し、グラブの構え位置・前腕露出・上体傾き・手の深さ・捕手ターゲットなど、ボールリリース前の投球癖を精密解析します。",
    hero_cov_curr_lbl: "現在の完了カバレッジ:",
    hero_cov_curr_val: "ナ・リーグ西地区（NL West）の全投手陣および先発ローテーションを100%解析・モデル化完了。",
    hero_cov_cap_lbl: "パイプライン全体の拡張対応力:",
    hero_cov_cap_val: "Synergy、TrackMan、または球場カメラ映像から直接、所属リーグ全体—MLB全30球団、NCAA Division I大学野球、NPB（日本）、KBO（韓国）、CPBL（台湾）、メキシコ（LMB）、ウィンターリーグを追跡・モデル化するフルスケールパイプライン能力。",
    hero_btn_roupp: "実例検証: ランデン・ループ投手 →",
    hero_btn_erod: "エドゥアルド・ロドリゲス投手 →",
    hero_btn_webb: "ローガン・ウェブ投手 →",
    hero_btn_burns: "NCAA: チェイス・バーンズ投手 →",
    hero_btn_sasaki: "NPB: 佐々木朗希投手 🇯🇵 →",
    hero_btn_choi: "KBO: 崔原態 (チェ・ウォンテ) 投手 🇰🇷 →",
    hero_btn_gulin: "CPBL: 古林睿煬 (グーリン・ルェイヤン) 投手 🇹🇼 →",
    hero_btn_rios: "LMB: ウィルマー・リオス投手 🇲🇽 →",
    hero_btn_schedule_audit: "パイロット申請・解析デモの予約 →",

    meta_domain_label: "ドメイン",
    meta_domain_val: "国際リーグ動作解析AI ショーケース",
    meta_coverage_label: "完了カバレッジ",
    meta_coverage_val: "NL West 全投手陣 100% 完了",
    meta_capabilities_label: "対応可能リーグ",
    meta_capabilities_val: "MLB全30球団, NCAA, NPB, KBO, CPBL, LMB",
    meta_pitchers_label: "検証投手",
    meta_pitchers_val: "佐々木朗希 (NPB), バーンズ (NCAA), チェ・ウォンテ (KBO), 古林睿煬 (CPBL), リオス (LMB), ループ (MLB)",
    meta_catcher_label: "検証捕手",
    meta_catcher_val: "ガブリエル・モレノ (ARI) バッテリー",
    meta_feed_label: "基本映像",
    meta_feed_val: "バックスクリーンCFカメラ & パ・リーグTV / Synergy 1080p60映像",
    meta_scope_label: "検出対象",
    meta_scope_val: "グラブ, 姿勢, 前腕, セット静止時間, 捕手構え",
    meta_window_label: "計測時間枠",
    meta_window_val: "セットポジション → ハンドブレイク (漏洩ゼロ)",

    filter_all_leagues: "全リーグ (9選手・バッテリー公開中)",
    filter_all_orgs: "全球団・チーム (12組織)",
    filter_nlwest: "MLB NL West (5球団)",
    filter_mlb: "MLB 🇺🇸 (メジャー)",
    filter_ncaa: "NCAA 🎓 (米大学D1)",
    filter_npb: "NPB 🇯🇵 (日本プロ野球)",
    filter_kbo: "KBO 🇰🇷 (韓国プロ野球)",
    filter_cpbl: "CPBL 🇹🇼 (台湾プロ野球)",
    filter_lmb: "LMB 🇲🇽 (メキシカンリーグ)",

    workflow_eyebrow: "実戦導入の4ステップ",
    workflow_h2: "AI動作検出からバッターボックスでの実戦攻略まで",
    workflow_lede: "大学野球部やプロ野球球団がAIによる動作差異検出をグラウンドでの勝利に結びつける流れ。",
    step1_num: "ステップ 01",
    step1_title: "AIモデルによる投球パターンの自動検出",
    step1_desc: "PreflightがSynergy映像や試合映像を自動取り込み、30箇所以上の生体力学ランドマークを追跡して球種ごとの物理的動作差異を特定します。",
    step2_num: "ステップ 02",
    step2_title: "アナリスト・スコアラーによる癖の検証",
    step2_desc: "データアナリストが球種割合、順列検定、複数試合のホールドアウト検証を通じて偶然の誤差を排除し、真の予測精度を確定します。",
    step3_num: "ステップ 03",
    step3_title: "コーチ陣による打者への視覚指導",
    step3_desc: "打撃コーチが検証済みの投球癖（グラブ位置、足の上げテンポ、捕手構えの高さ）をカウント別の狙い球戦略として打者に落とし込みます。",
    step4_num: "ステップ 04",
    step4_title: "選手によるグラウンドでの実戦実行",
    step4_desc: "打席のバッターや二塁走者がテイクバック前の動作で球種を瞬時に見極め、狙い球を絞って圧倒的な優位性を獲得します。",

    catcher_eyebrow: "バッテリー高度スカウティング実例",
    catcher_h2: "キャッチャーの構え・事前ターゲット位置の癖検知",
    catcher_lede: "癖はピッチャーだけではありません。Preflightは投球開始前の捕手のスタンス幅、ミットの構えの高さ、静止タイミングを追跡します。",
    catcher_moreno_title: "ガブリエル・モレノ (ARI · 捕手)",
    catcher_moreno_sub: "投球前ミット構えの高さ変化 & 構え静止タイミング (バッテリー解析)",
    catcher_stat1_lbl: "シグナル分離度",
    catcher_stat2_lbl: "ミット構え高さの差",
    catcher_stat3_lbl: "球種判別精度",
    catcher_stat4_lbl: "時間的情報漏洩",
    catcher_cue1_title: "1. 投球前のミット構え高さの偏り (ストレート vs チェンジアップ/スライダー):",
    catcher_cue1_desc: "フォーシーム直球時、モレノ捕手はミットを3.4インチ高く構えて静止します。チェンジアップやスライダー時には深く沈み込み、低めにミットをセットします。",
    catcher_cue2_title: "2. 足上げ前の捕手構え静止タイミングの違い:",
    catcher_cue2_desc: "変化球時、モレノ捕手は直球時よりも210ミリ秒早くミットを完全静止させます。これにより二塁走者やベンチが事前に球種を察知できます。",
    catcher_cta_more: "対戦相手の捕手構え・バッテリースカウティング監査を依頼 →",

    showcase_eyebrow: "国際リーグ動作差異プロファイル",
    showcase_h2: "検証済み 各国リーグ投球動作差異ショーケース (NCAA, NPB, KBO, CPBL, LMB, MLB)",
    showcase_lede: "日米韓台墨のトップ投手における物理的動作差異リード、高画質映像ソース、ホールドアウト検証済みの生体力学メトリクスを確認できます。",
    
    showcase_card_roupp_title: "ランデン・ループ · SFジャイアンツ (MLB 🇺🇸)",
    showcase_card_roupp_badge: "MLB ショーケース",
    showcase_card_roupp_desc: "カーブ (CU) vs シンカー (SI) / チェンジアップ (CH) の動作分析。足上げ頂点(-0.28s)でのグラブ上昇（カーブ時にユニフォーム胸文字を覆うほど高位置）およびセット時(-0.85s)のポケット内手首深度差異。",
    showcase_card_roupp_btn: "動作プロファイルを見る →",

    showcase_card_erod_title: "エドゥアルド・ロドリゲス · ARI (MLB 🇺🇸)",
    showcase_card_erod_badge: "MLB ショーケース",
    showcase_card_erod_desc: "チェンジアップ対カットボールでの膝引き上げテンポ（40球検証で+11.3%の予測リフト）およびストレート対シンカーでのグラブ速度変化。",
    showcase_card_erod_btn: "動作プロファイルを見る →",

    showcase_card_webb_title: "ローガン・ウェブ · SFジャイアンツ (MLB 🇺🇸)",
    showcase_card_webb_badge: "MLB ショーケース",
    showcase_card_webb_desc: "シンカー・直球とチェンジアップでの足上げ移行スピード差、およびセットポジションからのグラブ引き上げ幅の差異。",
    showcase_card_webb_btn: "動作プロファイルを見る →",

    showcase_card_burns_title: "チェイス・バーンズ · ウェイクフォレスト大 (NCAA 🎓)",
    showcase_card_burns_badge: "NCAA ショーケース",
    showcase_card_burns_desc: "フォーシーム直球 (FF) vs スライダー (SL) でのセット時のグラブ高さ差異（直球時に約2.8インチ高い位置でセット、信号強度88.5%、d=1.24）。",
    showcase_card_burns_btn: "NCAA動作分析を見る →",

    showcase_card_sasaki_title: "佐々木朗希 · 千葉ロッテマリーンズ (NPB 🇯🇵)",
    showcase_card_sasaki_badge: "NPB ショーケース",
    showcase_card_sasaki_desc: "フォークボール (FS) vs フォーシーム直球 (FF) でのセット静止時間・手首のグラブ挿入深度（フォーク時に静止時間が180ms長くグラブ角度も変化、信号強度91.2%、d=1.42）。",
    showcase_card_sasaki_btn: "NPB動作分析を見る →",

    showcase_card_choi_title: "崔原態 (チェ・ウォンテ) · LGツインズ (KBO 🇰🇷)",
    showcase_card_choi_badge: "KBO ショーケース",
    showcase_card_choi_desc: "チェンジアップ (CH) vs ツーシーム (SI) でのグラブ開き・足上げ前テンポ（チェンジアップの握りで親指側のグラブが140ms早く開く、信号強度87.8%、d=1.18）。",
    showcase_card_choi_btn: "KBO動作分析を見る →",

    showcase_card_gulin_title: "古林睿煬 (グーリン・ルェイヤン) · 統一ライオンズ (CPBL 🇹🇼)",
    showcase_card_gulin_badge: "CPBL ショーケース",
    showcase_card_gulin_desc: "カーブ (CU) vs フォーシーム直球 (FF) でのセット時グラブ高さ差異（カーブ時に肋骨中段、直球時に胸上部、信号強度89.4%、d=1.31）。",
    showcase_card_gulin_btn: "CPBL動作分析を見る →",

    showcase_card_rios_title: "ウィルマー・リオス · アセレロス・デ・モンクローバ (LMB 🇲🇽)",
    showcase_card_rios_badge: "LMB ショーケース",
    showcase_card_rios_desc: "シンカー (SI) vs スライダー (SL) / チェンジアップ (CH) でのセット時グラブ位置・手首角度（シンカー時にグラブが胸中段へ約2.6インチ高くセットされ手首が回内、スライダー時はベルト下段、信号強度88.2%、d=1.18）。",
    showcase_card_rios_btn: "LMB動作分析を見る →",

    roster_eyebrow: "国際リーグ・大学球団カバレッジ",
    roster_h2: "35名以上の検証済み投手 ＆ 対戦カード前スカウティングDB",
    roster_lede: "エンタープライズおよび大学向けパイロットで、MLB、NPB、KBO、CPBL、LMBのローテーション・ブルペン全陣容を網羅。",

    lock_banner_title: "🔒 スカウティングデータベース（エンタープライズ限定）",
    lock_banner_desc: "MLB、NPB、KBO、CPBL、メキシカンリーグ、大学D1の全60名以上の詳細投球動作ファイルを閲覧できます。",
    lock_banner_btn: "組織・球団向けパイロット申請 →",

    modal_badge: "🔒 守秘義務契約（NDA）に基づくパイロット申請",
    modal_title: "Preflight スカウティングパイロット申請",
    modal_desc: "2027年大学ライセンス（5,000〜15,000ドル）、カンファレンス独占権（18,000〜35,000ドル）、プロ球団向け導入プランについてのお問い合わせ。動画共有前に双方署名の秘密保持契約（NDA）を締結します。",
    modal_lbl_name: "お名前 *",
    modal_lbl_org: "ご所属（球団名・大学名） *",
    modal_lbl_email: "公式・業務メールアドレス *",
    modal_lbl_level: "カテゴリー / 所属リーグ *",
    modal_lbl_tier: "ご希望プラン *",
    modal_lbl_notes: "備考 / 特定の対戦相手・スケジュール",
    modal_submit: "パイロット申請を送信 →",
    modal_direct_email: "直接連絡先",
    modal_success_title: "パイロット申請ありがとうございます。",
    modal_success_body: "Colby Morris (colby.morris08@gmail.com) 宛てにメール下書きが作成されました。NDA締結と映像連携に向けて速やかにご連絡いたします。",

    footer_text: "Preflight コンピュータービジョン · 動作差異解析エンジン · 開発者 Colby Morris"
  },

  ko: {
    lang_toolbar_label: "언어 / Language:",
    brand_title: "Preflight",
    brand_sub: "컴퓨터 비전 · 글로벌 리그 쇼케이스",
    nav_overview: "개요",
    nav_coverage: "구단 커버리지",
    nav_leads: "동작 차이 순위",
    nav_pricing: "요금제 및 독점권",
    nav_arch: "비전 아키텍처",
    nav_request_pilot: "파일럿 신청",

    hero_eyebrow: "공개 쇼케이스 · KBO (한국), NPB, MLB, NCAA, CPBL, LMB 전력분석 인텔",
    hero_h1: "투구 버릇(피치 티핑) 및 포수 셋업 감지 컴퓨터 비전 AI",
    hero_desc: "Preflight는 글로벌 프로 및 대학 리그 영상에서 고해상도 랜드마크와 바운딩 박스를 자동 추적하여 글러브 높이, 전완 노출, 상체 기울기, 손 깊이, 포수 타깃 위치 등 투구 전 미세한 폼 차이를 정밀 분석합니다.",
    hero_cov_curr_lbl: "현재 완료된 커버리지:",
    hero_cov_curr_val: "NL 서부지구 전 구단 투수진 및 선발 로테이션 100% 모델링 완료.",
    hero_cov_cap_lbl: "전체 파이프라인 확장 역량:",
    hero_cov_cap_val: "Synergy, TrackMan 또는 구장 비디오 피드를 통해 소속 리그 전체—MLB 30개 구단 전체, NCAA Division I 대학 야구, NPB(일본), KBO(한국), CPBL(대만), 멕시코(LMB) 및 윈터리그를 직접 추적 및 모델링하는 풀스케일 파이프라인 역량 보유.",
    hero_btn_roupp: "실증 분석: 랜든 룹 투수 →",
    hero_btn_erod: "에두아르도 로드리게스 →",
    hero_btn_webb: "로건 웹 →",
    hero_btn_burns: "NCAA: 체이스 번스 →",
    hero_btn_sasaki: "NPB: 사사키 로키 🇯🇵 →",
    hero_btn_choi: "KBO: 최원태 (LG 트윈스) 🇰🇷 →",
    hero_btn_gulin: "CPBL: 구린루이양 🇹🇼 →",
    hero_btn_rios: "LMB: 윌머 리오스 🇲🇽 →",
    hero_btn_schedule_audit: "파일럿 신청 / 전력분석 세미나 예약 →",

    meta_domain_label: "도메인",
    meta_domain_val: "글로벌 컴퓨터 비전 쇼케이스",
    meta_coverage_label: "완료 커버리지",
    meta_coverage_val: "NL West 전 구단 100% 완료",
    meta_capabilities_label: "파이프라인 역량",
    meta_capabilities_val: "MLB 30개 구단, NCAA, NPB, KBO, CPBL, LMB",
    meta_pitchers_label: "검증 투수",
    meta_pitchers_val: "최원태 (KBO), 사사키 (NPB), 번스 (NCAA), 구린 (CPBL), 리오스 (LMB), 룹 (MLB)",
    meta_catcher_label: "검증 포수",
    meta_catcher_val: "가브리엘 모레노 (ARI) 배터리",
    meta_feed_label: "기본 영상",
    meta_feed_val: "중계 CF 카메라 & SPOTV / Synergy 1080p60 피드",
    meta_scope_label: "감지 영역",
    meta_scope_val: "글러브, 자세, 전완, 세트 정지 시간, 포수 셋업",
    meta_window_label: "측정 시간대",
    meta_window_val: "세트 포지션 → 핸드 브레이크 (0초 정보 누출)",

    filter_all_leagues: "전체 리그 (9개 프로필 공개)",
    filter_all_orgs: "전체 구단 (12개)",
    filter_nlwest: "MLB NL 서부 (5개)",
    filter_mlb: "MLB 🇺🇸 (메이저리그)",
    filter_ncaa: "NCAA 🎓 (미국 대학 D1)",
    filter_npb: "NPB 🇯🇵 (일본 프로야구)",
    filter_kbo: "KBO 🇰🇷 (한국 프로야구)",
    filter_cpbl: "CPBL 🇹🇼 (대만 프로야구)",
    filter_lmb: "LMB 🇲🇽 (멕시칸 리그)",

    workflow_eyebrow: "4단계 전력분석 파이프라인",
    workflow_h2: "AI 동작 감지에서 타석 내 실전 공략까지",
    workflow_lede: "대학 야구부와 프로 야구단이 컴퓨터 비전 동작 차이 분석을 실전 승리로 연결하는 과정.",
    step1_num: "STEP 01",
    step1_title: "AI 모델의 투구 패턴 자동 탐지",
    step1_desc: "Preflight가 경기 및 중계 영상을 자동 수집하여 30개 이상의 생체역학 랜드마크를 추적하고 구종별 물리적 동작 차이를 분리합니다.",
    step2_num: "STEP 02",
    step2_title: "전력분석원의 투구 습관 검증",
    step2_desc: "구종 비율, 순열 검정, 다중 경기 홀드아웃 검증을 통해 우연한 오차를 제거하고 실제 타격 유효성을 확인합니다.",
    step3_num: "STEP 03",
    step3_title: "코칭스태프의 시각 인지 지도",
    step3_desc: "타격 코치가 검증된 투구 습관(글러브 높이, 레그킥 템포, 포수 타깃 위치)을 카운트별 노림수 전략으로 선수단에 전수합니다.",
    step4_num: "STEP 04",
    step4_title: "선수단의 그라운드 실전 실행",
    step4_desc: "타석의 타자와 2루 주자가 투구 모션 초기 단계에서 구종을 포착하여 노림수를 좁히고 타격 생산성을 극대화합니다.",

    catcher_eyebrow: "배터리 전력분석 실전 사례",
    catcher_h2: "포수 투구 전 타깃 위치 및 셋업 동작 습관 감지",
    catcher_lede: "구종 노출은 투수만의 문제가 아닙니다. Preflight는 투구 시작 전 포수의 스탠스 폭, 미트 높이, 정지 타이밍을 추적합니다.",
    catcher_moreno_title: "가브리엘 모레노 (ARI · 포수)",
    catcher_moreno_sub: "투구 전 미트 타깃 높이 변화 및 셋업 정지 타이밍 (배터리 분석)",
    catcher_stat1_lbl: "신호 분리도",
    catcher_stat2_lbl: "미트 타깃 이동폭",
    catcher_stat3_lbl: "구종 판별률",
    catcher_stat4_lbl: "시간적 정보 누출",
    catcher_cue1_title: "1. 투구 전 미트 타깃 높이 편차 (패스트볼 vs 체인지업/슬라이더):",
    catcher_cue1_desc: "포심 패스트볼 시 모레노 포수는 미트를 3.4인치 높게 유지합니다. 체인지업과 슬라이더 시에는 더 깊게 앉아 미트를 낮게 설정합니다.",
    catcher_cue2_title: "2. 레그킥 시작 전 포수 셋업 정지 타이밍:",
    catcher_cue2_desc: "변화구 선택 시 모레노 포수는 직구 대비 210ms 일찍 미트를 완전 정지시켜 2루 주자와 벤치에 확실한 사전 신호를 제공합니다.",
    catcher_cta_more: "상대팀 포수 셋업 및 배터리 전력분석 요청 →",

    showcase_eyebrow: "글로벌 리그 동작 차이 프로필",
    showcase_h2: "검증된 각국 리그 투구 습관 쇼케이스 (NCAA, NPB, KBO, CPBL, LMB, MLB)",
    showcase_lede: "글로벌 프로 및 대학 리그 에이스 투수들의 생체역학적 동작 차이와 고해상도 방송 분석 데이터를 확인하세요.",
    
    showcase_card_roupp_title: "랜든 룹 · SF 자이언츠 (MLB 🇺🇸)",
    showcase_card_roupp_badge: "MLB 쇼케이스",
    showcase_card_roupp_desc: "커브(CU) vs 싱커(SI) 및 체인지업(CH) 투구폼 분석. 레그킥 정점(-0.28s) 시 유니폼 가슴 로고를 덮는 글러브 상승량 차이 및 셋 포지션(-0.85s) 시 손목 삽입 깊이 차이.",
    showcase_card_roupp_btn: "동작 프로파일 보기 →",

    showcase_card_erod_title: "에두아르도 로드리게스 · ARI (MLB 🇺🇸)",
    showcase_card_erod_badge: "MLB 쇼케이스",
    showcase_card_erod_desc: "체인지업 vs 커터 무릎 상승 템포(+11.3% 예측 향상) 및 포심 vs 싱커 글러브 속도 차이.",
    showcase_card_erod_btn: "동작 프로파일 보기 →",

    showcase_card_webb_title: "로건 웹 · SF 자이언츠 (MLB 🇺🇸)",
    showcase_card_webb_badge: "MLB 쇼케이스",
    showcase_card_webb_desc: "싱커/포심 대비 체인지업 시 레그킥 전환 속도 차이 및 셋 포지션 글러브 상승폭 차이.",
    showcase_card_webb_btn: "동작 프로파일 보기 →",

    showcase_card_burns_title: "체이스 번스 · 웨이크 포레스트 대 (NCAA 🎓)",
    showcase_card_burns_badge: "NCAA 쇼케이스",
    showcase_card_burns_desc: "포심 패스트볼(FF) vs 슬라이더(SL) 셋 포지션 글러브 높이 차이(직구 시 2.8인치 높게 셋업, 판별률 88.5%, d=1.24).",
    showcase_card_burns_btn: "NCAA 분석 보기 →",

    showcase_card_sasaki_title: "사사키 로키 · 지바 롯데 마린스 (NPB 🇯🇵)",
    showcase_card_sasaki_badge: "NPB 쇼케이스",
    showcase_card_sasaki_desc: "포크볼(FS) vs 포심 직구(FF) 셋 정지 시간 및 손목 글러브 삽입 깊이(포크볼 그립 시 정지 시간 180ms 증가, 판별률 91.2%, d=1.42).",
    showcase_card_sasaki_btn: "NPB 분석 보기 →",

    showcase_card_choi_title: "최원태 · LG 트윈스 (KBO 🇰🇷)",
    showcase_card_choi_badge: "KBO 쇼케이스",
    showcase_card_choi_desc: "체인지업(CH) vs 투심 싱커(SI) 글러브 플레어 및 레그킥 전 템포(체인지업 그립 시 엄지 쪽 글러브가 140ms 일찍 벌어짐, 판별률 87.8%, d=1.18).",
    showcase_card_choi_btn: "KBO 분석 보기 →",

    showcase_card_gulin_title: "구린루이양 · 퉁이 라이온즈 (CPBL 🇹🇼)",
    showcase_card_gulin_badge: "CPBL 쇼케이스",
    showcase_card_gulin_desc: "커브(CU) vs 직구(FF) 셋 포지션 글러브 위치 차이(커브 시 갈비뼈 중단, 직구 시 흉부 상단, 판별률 89.4%, d=1.31).",
    showcase_card_gulin_btn: "CPBL 분석 보기 →",

    showcase_card_rios_title: "윌머 리오스 · 아세레로스 데 몬클로바 (LMB 🇲🇽)",
    showcase_card_rios_badge: "LMB 쇼케이스",
    showcase_card_rios_desc: "싱커(SI) vs 슬라이더(SL)/체인지업(CH) 셋 포지션 글러브 높이 및 손목 각도 차이(싱커 시 글러브를 2.6인치 높게 중흉부에 셋업 및 손목 회내 vs 슬라이더 시 벨트라인 셋업, 판별률 88.2%, d=1.18).",
    showcase_card_rios_btn: "LMB 분석 보기 →",

    roster_eyebrow: "글로벌 프로 및 대학 리그 전체 커버리지",
    roster_h2: "35명 이상의 검증된 투수진 및 시리즈 대비 데이터베이스",
    roster_lede: "엔터프라이즈 및 대학 파일럿을 통해 MLB, NPB, KBO, CPBL, LMB 전 구단 선발/불펜진 열람 가능.",

    lock_banner_title: "🔒 전력분석 데이터베이스 잠금 (엔터프라이즈 전용)",
    lock_banner_desc: "MLB, NPB, KBO, CPBL, 멕시칸 리그, NCAA D1 등 60명 이상의 투수 및 포수 전체 프로필에 접근하세요.",
    lock_banner_btn: "엔터프라이즈 파일럿 신청 →",

    modal_badge: "🔒 비밀유지협약(NDA) 기반 파일럿 신청",
    modal_title: "Preflight 전력분석 파일럿 및 접근 권한 신청",
    modal_desc: "2027년 대학 라이선스(k–k), 콘퍼런스 독점권(k–k) 또는 프로 구단 도입 문의. 영상 공유 전 상호 서명된 비밀유지협약(NDA)을 체결합니다.",
    modal_lbl_name: "성함 *",
    modal_lbl_org: "소속 구단 / 대학명 *",
    modal_lbl_email: "공식 / 업무용 이메일 *",
    modal_lbl_level: "소속 리그 / 디비전 *",
    modal_lbl_tier: "관심 요금제 *",
    modal_lbl_notes: "특정 분석 대상 구단 / 일정 등",
    modal_submit: "파일럿 신청서 제출 →",
    modal_direct_email: "직접 문의 이메일",
    modal_success_title: "파일럿 신청이 접수되었습니다.",
    modal_success_body: "Colby Morris (colby.morris08@gmail.com) 앞으로 이메일이 준비되었습니다. NDA 체결 및 영상 연동을 위해 신속히 회신드리겠습니다.",

    footer_text: "Preflight 컴퓨터 비전 · 피치 티핑 및 셋업 분석 엔진 · 개발자 Colby Morris"
  },

  es: {
    lang_toolbar_label: "Idioma / Language / 言語 / 언어 / 語言:",
    brand_title: "Preflight",
    brand_sub: "Visión por Computadora · Muestra Multi-Liga",
    nav_overview: "Resumen",
    nav_coverage: "Tablero de Cobertura",
    nav_leads: "Diferencias Clasificadas",
    nav_pricing: "Precios y Exclusividad",
    nav_arch: "Arquitectura y CV",
    nav_request_pilot: "Solicitar Piloto",

    hero_eyebrow: "Muestra Pública · Inteligencia de Scouting Avanzado LMB, MLB, NCAA, NPB, KBO y CPBL",
    hero_h1: "Motor de Visión por Computadora para Detección de Inclinación de Pitcheo y Variaciones Mecánicas.",
    hero_desc: "Preflight automatiza el rastreo de puntos anatómicos y cajas delimitadoras de alta resolución para detectar variaciones mecánicas lanzamiento a lanzamiento (altura del guante, exposición del antebrazo, inclinación del torso, profundidad de la mano y ubicación del receptor) estrictamente antes de soltar la pelota.",
    hero_cov_curr_lbl: "Cobertura Actual Completada:",
    hero_cov_curr_val: "100% de los cuerpos de lanzadores y rotaciones de la División Oeste de la Liga Nacional (NL West) completados y modelados.",
    hero_cov_cap_lbl: "Capacidades Completas del Sistema:",
    hero_cov_cap_val: "Capacidades de procesamiento a escala completa para rastrear y modelar toda su liga respectiva: MLB (los 30 clubes), Béisbol Universitario NCAA División I, NPB (Japón), KBO (Corea), CPBL (Taiwán), México (LMB) y Ligas Invernales directamente desde Synergy, TrackMan o señales de video del estadio.",
    hero_btn_roupp: "Explorar Muestra: Landen Roupp →",
    hero_btn_erod: "Eduardo Rodriguez →",
    hero_btn_webb: "Logan Webb →",
    hero_btn_burns: "NCAA: Chase Burns →",
    hero_btn_sasaki: "NPB: Roki Sasaki 🇯🇵 →",
    hero_btn_choi: "KBO: Won-tae Choi 🇰🇷 →",
    hero_btn_gulin: "CPBL: Gu Lin Ruei-Yang 🇹🇼 →",
    hero_btn_rios: "LMB: Wilmer Ríos 🇲🇽 →",
    hero_btn_schedule_audit: "Solicitar Piloto / Programar Auditoría →",

    meta_domain_label: "Dominio",
    meta_domain_val: "Muestra de Visión por Computadora",
    meta_coverage_label: "Cobertura Completada",
    meta_coverage_val: "100% NL West Modelado",
    meta_capabilities_label: "Capacidad del Pipeline",
    meta_capabilities_val: "MLB (30 Clubes), NCAA, NPB, KBO, CPBL, LMB",
    meta_pitchers_label: "Lanzadores en Muestra",
    meta_pitchers_val: "Ríos (LMB), Sasaki (NPB), Burns (NCAA), Choi (KBO), Gu Lin (CPBL), Roupp (MLB)",
    meta_catcher_label: "Receptor en Muestra",
    meta_catcher_val: "Batería de Gabriel Moreno (ARI)",
    meta_feed_label: "Transmisión Base",
    meta_feed_val: "Cámara Center-Field (CF) y Jonron TV / Synergy 1080p60",
    meta_scope_label: "Alcance",
    meta_scope_val: "Guante, Postura, Antebrazo, Tiempo en Set, Receptor",
    meta_window_label: "Ventana de Acción",
    meta_window_val: "Posición de Set → Quiebre de Manos (0s Fuga)",

    filter_all_leagues: "Todas las Ligas (9 Perfiles Desbloqueados)",
    filter_all_orgs: "Todas las Organizaciones (12)",
    filter_nlwest: "Enfoque NL Oeste (5 Clubes)",
    filter_mlb: "MLB 🇺🇸 (Grandes Ligas)",
    filter_ncaa: "NCAA 🎓 (Colegial D1)",
    filter_npb: "NPB 🇯🇵 (Japón)",
    filter_kbo: "KBO 🇰🇷 (Corea)",
    filter_cpbl: "CPBL 🇹🇼 (Taiwán)",
    filter_lmb: "LMB 🇲🇽 (Liga Mexicana de Béisbol)",

    workflow_eyebrow: "El Proceso Operativo de 4 Pasos",
    workflow_h2: "De la Detección por IA a la Ejecución en la Caja de Bateo",
    workflow_lede: "Cómo los programas colegiales y franquicias profesionales convierten la visión artificial en victorias reales.",
    step1_num: "PASO 01",
    step1_title: "El Modelo Encuentra el Patrón",
    step1_desc: "Preflight procesa videos de transmisión y Synergy, rastreando más de 30 puntos biomecánicos para aislar diferencias entre lanzamientos.",
    step2_num: "PASO 02",
    step2_title: "Los Analistas Confirman la Señal",
    step2_desc: "Scouts y analistas cuantitativos validan la señal contra la mezcla de lanzamientos y pruebas de permutación para eliminar el ruido.",
    step3_num: "PASO 03",
    step3_title: "Los Coaches Enseñan el Reconocimiento",
    step3_desc: "Los coaches de bateo transforman las señales validadas en detonantes visuales claros y planes por conteo.",
    step4_num: "PASO 04",
    step4_title: "Los Jugadores Ejecutan en el Terreno",
    step4_desc: "Los bateadores y corredores en segunda base reconocen el lanzamiento antes de acelerar el brazo, eliminando pitcheos secundarios.",

    catcher_eyebrow: "Inteligencia Real de Batería",
    catcher_h2: "Señales en la Preparación y Colocación del Receptor",
    catcher_lede: "Los lanzadores no son los únicos que muestran señales. Preflight rastrea el ancho de postura, la altura del guante y el tiempo de quietud del receptor.",
    catcher_moreno_title: "Gabriel Moreno (ARI Diamondbacks · Receptor)",
    catcher_moreno_sub: "Elevación del Guante y Tiempo de Quietud en la Agachada (Análisis de Batería NL West)",
    catcher_stat1_lbl: "Separación de Señal",
    catcher_stat2_lbl: "Desplazamiento del Guante",
    catcher_stat3_lbl: "Tasa de Discriminación",
    catcher_stat4_lbl: "Fuga Temporal",
    catcher_cue1_title: "1. Cambio de Altura en el Objetivo del Guante (Recta vs Cambio/Slider):",
    catcher_cue1_desc: "En rectas de 4 costuras, Moreno coloca su guante 3.4 pulgadas más alto. En cambios y sliders, se agacha más profundo y prepara bajo.",
    catcher_cue2_title: "2. Tiempo de Quietud Previo a la Elevación de la Pierna:",
    catcher_cue2_desc: "En lanzamientos rompientes, Moreno logra quietud total 210 ms antes que en rectas, dando a los corredores y dugout una señal clara.",
    catcher_cta_more: "Solicitar Auditoría Completa de Receptores Rivales →",

    showcase_eyebrow: "Dossiers de Muestra Global",
    showcase_h2: "Diferencias Mecánicas Verificadas en Ligas Globales (NCAA, NPB, KBO, CPBL, LMB, MLB)",
    showcase_lede: "Examine las principales diferencias biomecánicas, fuentes de video y métricas validadas.",
    
    showcase_card_roupp_title: "Landen Roupp · SF Giants (MLB 🇺🇸)",
    showcase_card_roupp_badge: "MUESTRA MLB",
    showcase_card_roupp_desc: "Curva (CU) vs Sinker (SI) y Cambio (CH). Elevación del guante en el ápice de la pierna (-0.28s cubriendo las letras del jersey en CU) y profundidad de muñeca en el guante al set (-0.85s).",
    showcase_card_roupp_btn: "Ver Perfil de Lanzamiento →",

    showcase_card_erod_title: "Eduardo Rodriguez · ARI (MLB 🇺🇸)",
    showcase_card_erod_badge: "MUESTRA MLB",
    showcase_card_erod_desc: "Ritmo de elevación de rodilla (+11.3% de mejora predictiva en CH vs FC) y velocidad del guante en FF vs SI.",
    showcase_card_erod_btn: "Ver Perfil de Lanzamiento →",

    showcase_card_webb_title: "Logan Webb · SF Giants (MLB 🇺🇸)",
    showcase_card_webb_badge: "MUESTRA MLB",
    showcase_card_webb_desc: "Velocidad de transición al levantar la pierna en Cambio vs rectas/sinkers y elevación del guante desde el set.",
    showcase_card_webb_btn: "Ver Perfil de Lanzamiento →",

    showcase_card_burns_title: "Chase Burns · Wake Forest (NCAA 🎓)",
    showcase_card_burns_badge: "MUESTRA NCAA",
    showcase_card_burns_desc: "Recta de 4 costuras (FF) vs Slider (SL) en la altura del guante al colocarse en set (+2.8 in más alto en FF, 88.5% señal, d=1.24).",
    showcase_card_burns_btn: "Ver Análisis NCAA →",

    showcase_card_sasaki_title: "Roki Sasaki · Chiba Lotte (NPB 🇯🇵)",
    showcase_card_sasaki_badge: "MUESTRA NPB",
    showcase_card_sasaki_desc: "Forkball/Splitter (FS) vs Recta (FF) en tiempo de pausa y profundidad de muñeca (+180ms de pausa extra en splitter, 91.2% señal, d=1.42).",
    showcase_card_sasaki_btn: "Ver Análisis NPB →",

    showcase_card_choi_title: "Won-tae Choi · LG Twins (KBO 🇰🇷)",
    showcase_card_choi_badge: "MUESTRA KBO",
    showcase_card_choi_desc: "Cambio (CH) vs Sinker (SI) en apertura del guante y tempo previo al movimiento (el guante se abre 140ms antes en cambio, 87.8% señal, d=1.18).",
    showcase_card_choi_btn: "Ver Análisis KBO →",

    showcase_card_gulin_title: "Gu Lin Ruei-Yang · Uni-Lions (CPBL 🇹🇼)",
    showcase_card_gulin_badge: "MUESTRA CPBL",
    showcase_card_gulin_desc: "Curva (CU) vs Recta (FF) en la altura del guante al set (costillas medias en curva vs pecho alto en recta, 89.4% señal, d=1.31).",
    showcase_card_gulin_btn: "Ver Análisis CPBL →",

    showcase_card_rios_title: "Wilmer Ríos · Acereros de Monclova (LMB 🇲🇽)",
    showcase_card_rios_badge: "MUESTRA LMB",
    showcase_card_rios_desc: "Sinker (SI) vs Slider (SL) / Cambio (CH) en altura de presentación del guante y orientación de muñeca (+2.6 in más alto en el pecho medio en sinker con muñeca pronada vs línea del cinturón en slider, 88.2% señal, d=1.18).",
    showcase_card_rios_btn: "Ver Análisis LMB →",

    roster_eyebrow: "Cobertura Global de Ligas y Universidades",
    roster_h2: "Más de 35 Lanzadores Auditados y Base de Datos Completa",
    roster_lede: "Rotaciones completas y bullpens disponibles mediante pilotos para organizaciones y universidades.",

    lock_banner_title: "🔒 Base de Datos de Scouting Bloqueada (Enterprise)",
    lock_banner_desc: "Acceda a más de 60 lanzadores y receptores en MLB, NPB, KBO, CPBL, LMB y NCAA D1.",
    lock_banner_btn: "Solicitar Acceso Piloto →",

    modal_badge: "🔒 Solicitud de Piloto Confidencial",
    modal_title: "Solicitar Piloto de Scouting Preflight",
    modal_desc: "Consulte sobre licencias colegiales 2027 (k–k), exclusividad de conferencia (k–k) o implementaciones profesionales. Se firma un acuerdo de confidencialidad mutuo (NDA).",
    modal_lbl_name: "Nombre Completo *",
    modal_lbl_org: "Organización / Universidad *",
    modal_lbl_email: "Correo Institucional / Profesional *",
    modal_lbl_level: "Nivel / Liga *",
    modal_lbl_tier: "Plan de Interés *",
    modal_lbl_notes: "Notas / Rivales Específicos",
    modal_submit: "Enviar Solicitud de Piloto →",
    modal_direct_email: "Correo Directo",
    modal_success_title: "Gracias por su solicitud.",
    modal_success_body: "Se ha preparado un correo electrónico dirigido a Colby Morris (colby.morris08@gmail.com). Responderemos a la brevedad.",

    footer_text: "Preflight Visión por Computadora · Detección de Inclinación de Pitcheo · Creado por Colby Morris"
  },

  "zh-TW": {
    lang_toolbar_label: "語言 / Language / 言語 / 언어 / Idioma:",
    brand_title: "Preflight",
    brand_sub: "電腦視覺 · 全球聯賽展示版",
    nav_overview: "總覽",
    nav_coverage: "球隊覆蓋率",
    nav_leads: "動作差異排行",
    nav_pricing: "定價與獨家權",
    nav_arch: "技術架構與CV",
    nav_request_pilot: "申請試用專案",

    hero_eyebrow: "公開展示版 · 中華職棒 (CPBL), 日本職棒 (NPB), 韓職 (KBO), 美國職棒 (MLB), 墨職 (LMB), 美國大學 (NCAA) 情蒐情資",
    hero_h1: "抓小動作（投球癖性）與捕手蹲捕站位偵測 電腦視覺 AI 引擎",
    hero_desc: "Preflight 自動追蹤全球聯賽高解析度人體骨架關鍵點與物件辨識框，在投手放球前精準比對手套設定高度、前臂露出、軀幹前傾、手在手套深淺及捕手設定位置等微小動作差異。",
    hero_cov_curr_lbl: "目前已完成覆蓋率:",
    hero_cov_curr_val: "國聯西區（NL West）全體投手陣容與先發輪值已 100% 完成電腦視覺建模。",
    hero_cov_cap_lbl: "完整系統管道擴展能力:",
    hero_cov_cap_val: "具備完整規模的運算管道能力，可直接透過 Synergy、TrackMan 或球場多角度影片，追蹤並建模您所在的整個聯賽——MLB（全部 30 支球團）、NCAA 一級大學棒球、NPB（日本職棒）、KBO（韓國職棒）、CPBL（中華職棒）、墨西哥聯盟（LMB）及冬季聯盟。",
    hero_btn_roupp: "實例分析：Landen Roupp 投手 →",
    hero_btn_erod: "Eduardo Rodriguez 投手 →",
    hero_btn_webb: "Logan Webb 投手 →",
    hero_btn_burns: "NCAA: Chase Burns 投手 →",
    hero_btn_sasaki: "NPB: 佐佐木朗希 🇯🇵 →",
    hero_btn_choi: "KBO: 崔原態 🇰🇷 →",
    hero_btn_gulin: "CPBL: 古林睿煬 (統一獅) 🇹🇼 →",
    hero_btn_rios: "LMB: 威爾默·里歐斯 🇲🇽 →",
    hero_btn_schedule_audit: "申請試用專案 / 預約情蒐審查 →",

    meta_domain_label: "領域",
    meta_domain_val: "全球電腦視覺展示平台",
    meta_coverage_label: "已完成覆蓋",
    meta_coverage_val: "NL West 投手陣 100% 建模",
    meta_capabilities_label: "管道處理能力",
    meta_capabilities_val: "MLB 全 30 球團、NCAA、NPB、KBO、CPBL、LMB",
    meta_pitchers_label: "展示投手",
    meta_pitchers_val: "古林睿煬 (CPBL), 佐佐木朗希 (NPB), Burns (NCAA), 崔原態 (KBO), 里歐斯 (LMB), Roupp (MLB)",
    meta_catcher_label: "展示捕手",
    meta_catcher_val: "Gabriel Moreno (ARI) 投捕搭檔",
    meta_feed_label: "基礎影像",
    meta_feed_val: "中外野 CF 轉播視角 & CPBL TV / Synergy 1080p60 訊號",
    meta_scope_label: "偵測範疇",
    meta_scope_val: "手套, 軀幹姿態, 前臂, 停留時間, 捕手蹲捕",
    meta_window_label: "有效動作窗口",
    meta_window_val: "就位 (Set) → 雙手分開 (0秒洩漏)",

    filter_all_leagues: "全部聯賽 (9位已解鎖展示)",
    filter_all_orgs: "全部球團/學校 (12個組織)",
    filter_nlwest: "MLB 國聯西區 (5隊)",
    filter_mlb: "MLB 🇺🇸 (美國職棒)",
    filter_ncaa: "NCAA 🎓 (美國大學D1)",
    filter_npb: "NPB 🇯🇵 (日本職棒)",
    filter_kbo: "KBO 🇰🇷 (韓國職棒)",
    filter_cpbl: "CPBL 🇹🇼 (中華職棒)",
    filter_lmb: "LMB 🇲🇽 (墨西哥聯盟)",

    workflow_eyebrow: "四步驟實戰導入流程",
    workflow_h2: "從 AI 自動動作辨識到打擊區實戰狙擊",
    workflow_lede: "大學棒球隊與職業球團如何將電腦視覺差異偵測轉化為球場上的實質勝場。",
    step1_num: "步驟 01",
    step1_title: "AI 模型自動捕捉投球模式",
    step1_desc: "Preflight 自動匯入 Synergy 與賽事轉播影片，追蹤 30+ 處生物力學骨架關鍵點，分離各球種間的物理動作差異。",
    step2_num: "步驟 02",
    step2_title: "情蒐分析師確認動作癖性",
    step2_desc: "進階情蒐與數據分析師透過球種配比、置換檢定及多場保留樣本驗證排除隨機雜訊，確立真實預測力。",
    step3_num: "步驟 03",
    step3_title: "教練團指導打者視覺識別",
    step3_desc: "打擊教練將經過驗證的動作線索（手套高度、抬腿節奏、捕手目標高度）轉化為清晰的視覺觸發點與球數策略。",
    step4_num: "步驟 04",
    step4_title: "選手於場上即時鎖定執行",
    step4_desc: "打擊區上的打者與二壘跑者在手臂加速前即時辨識球種，排除次要球路並精準出棒。",

    catcher_eyebrow: "真實投捕搭檔情蒐實例",
    catcher_h2: "捕手投球前準備動作與目標手套位置線索",
    catcher_lede: "洩漏球種的不只是投手。Preflight 追蹤投手啟動前捕手的站姿寬度、手套目標高度及靜止時機。",
    catcher_moreno_title: "Gabriel Moreno (ARI 響尾蛇 · 捕手)",
    catcher_moreno_sub: "投球前手套目標高度偏移與蹲捕靜止時間點 (國聯西區投捕分析)",
    catcher_stat1_lbl: "訊號分離度",
    catcher_stat2_lbl: "手套目標偏移量",
    catcher_stat3_lbl: "球種判別率",
    catcher_stat4_lbl: "時序資訊洩漏",
    catcher_cue1_title: "1. 投球前手套目標高度偏移 (四縫線速球 vs 變速球/滑球)：",
    catcher_cue1_desc: "面對四縫線速球時，Moreno 在就位時將目標手套固定在高出 3.4 英吋處。面對變速球與滑球時，他會更深蹲並提早擺低。",
    catcher_cue2_title: "2. 投手抬腿前捕手站姿完全靜止的時機：",
    catcher_cue2_desc: "在變化球配球時，Moreno 比速球時提早 210 毫秒達到完全靜止，提供二壘跑者與休息區明確的提前預警。",
    catcher_cta_more: "申請對手捕手與投捕搭檔情蒐審查 →",

    showcase_eyebrow: "全球聯賽動作差異檔案",
    showcase_h2: "已驗證 全球聯賽投手動作差異展示 (NCAA, NPB, KBO, CPBL, LMB, MLB)",
    showcase_lede: "檢視全球各聯賽指標投手的動作差異線索、高畫質轉播來源及保留樣本驗證之數據。",
    
    showcase_card_roupp_title: "Landen Roupp · 舊金山巨人 (MLB 🇺🇸)",
    showcase_card_roupp_badge: "MLB 展示",
    showcase_card_roupp_desc: "曲球 (CU) 與 伸卡球 (SI) / 變速球 (CH) 動作拆解。抬腿頂點(-0.28s)時手套上升幅度（曲球時手套高於球衣胸前文字）以及就位(-0.85s)時手腕深入手套深度差異。",
    showcase_card_roupp_btn: "檢視動作特徵拆解 →",

    showcase_card_erod_title: "Eduardo Rodriguez · 響尾蛇 (MLB 🇺🇸)",
    showcase_card_erod_badge: "MLB 展示",
    showcase_card_erod_desc: "變速球對卡特球時抬膝持續節奏（40球樣本中提升+11.3%預測力）及速球對伸卡球時手套速度差異。",
    showcase_card_erod_btn: "檢視動作特徵拆解 →",

    showcase_card_webb_title: "Logan Webb · 舊金山巨人 (MLB 🇺🇸)",
    showcase_card_webb_badge: "MLB 展示",
    showcase_card_webb_desc: "變速球相對於伸卡球/速球進入抬腿過渡的啟動速度，以及從就位姿勢上升的手套幅度差異。",
    showcase_card_webb_btn: "檢視動作特徵拆解 →",

    showcase_card_burns_title: "Chase Burns · 威克森林大學 (NCAA 🎓)",
    showcase_card_burns_badge: "NCAA 展示",
    showcase_card_burns_desc: "四縫線快速球 (FF) vs 滑球 (SL) 手套設定高度差異（快速球時手套高約2.8英吋，判別率 88.5%，d=1.24）。",
    showcase_card_burns_btn: "檢視 NCAA 分析 →",

    showcase_card_sasaki_title: "佐佐木朗希 · 千葉羅德海洋 (NPB 🇯🇵)",
    showcase_card_sasaki_badge: "NPB 展示",
    showcase_card_sasaki_desc: "指叉球 (FS) vs 四縫線快速球 (FF) 就位停留時間與手腕深入手套深度（指叉球握球時停留時間長180ms，判別率 91.2%，d=1.42）。",
    showcase_card_sasaki_btn: "檢視 NPB 分析 →",

    showcase_card_choi_title: "崔原態 · LG 雙子 (KBO 🇰🇷)",
    showcase_card_choi_badge: "KBO 展示",
    showcase_card_choi_desc: "變速球 (CH) vs 二縫線伸卡球 (SI) 手套外翻開口與抬腿前節奏（變速球握法使手套大拇指側提前140ms外張，判別率 87.8%，d=1.18）。",
    showcase_card_choi_btn: "檢視 KBO 分析 →",

    showcase_card_gulin_title: "古林睿煬 · 統一 7-ELEVEn 獅 (CPBL 🇹🇼)",
    showcase_card_gulin_badge: "CPBL 展示",
    showcase_card_gulin_desc: "曲球 (CU) vs 四縫線快速球 (FF) 就位手套高度偏移（曲球時手套置於肋骨中段，速球時置於胸口上方，判別率 89.4%，d=1.31）。",
    showcase_card_gulin_btn: "檢視 CPBL 分析 →",

    showcase_card_rios_title: "威爾默·里歐斯 · 蒙克洛瓦鐵人 (LMB 🇲🇽)",
    showcase_card_rios_badge: "LMB 展示",
    showcase_card_rios_desc: "伸卡球 (SI) vs 滑球 (SL) / 變速球 (CH) 就位手套設定高度與手腕角度差異（伸卡球手套高約 2.6 英吋置於胸口中段且手腕內旋，滑球則置於腰帶位置，判別率 88.2%，d=1.18）。",
    showcase_card_rios_btn: "檢視 LMB 分析 →",

    roster_eyebrow: "全球職業聯賽與大學隊伍完整覆蓋",
    roster_h2: "35位以上已審查投手 & 系列賽事前瞻情蒐資料庫",
    roster_lede: "企業版與大學專案支援完整輪值、牛棚及對手情蒐數據。",

    lock_banner_title: "🔒 企業情蒐資料庫鎖定",
    lock_banner_desc: "解鎖 60+ 位 MLB, NPB, KBO, CPBL, 墨西哥聯盟及 NCAA D1 完整球員檔案。",
    lock_banner_btn: "申請企業試用授權 →",

    modal_badge: "🔒 機密情蒐專案申請",
    modal_title: "申請 Preflight 情蒐試用專案與權限",
    modal_desc: "洽詢 2027 年大學授權方案（5,000–15,000 美元區間）、聯盟獨家鎖定授權（18,000–35,000 美元區間）或職業球團部署。影片分享前將簽署雙方保密協定（NDA）。",
    modal_lbl_name: "姓名 *",
    modal_lbl_org: "所屬單位 / 學校 / 球團 *",
    modal_lbl_email: "官方 / 公務電子郵件 *",
    modal_lbl_level: "層級 / 聯賽 *",
    modal_lbl_tier: "感興趣的方案 *",
    modal_lbl_notes: "備註 / 特定對手 / 時程規劃",
    modal_submit: "送出專案申請 →",
    modal_direct_email: "直接聯絡信箱",
    modal_success_title: "感謝您的申請。",
    modal_success_body: "已為您準備好致 Colby Morris (colby.morris08@gmail.com) 的信件草稿。我們將儘速與您聯繫簽署 NDA 與影片對接。",

    footer_text: "Preflight 電腦視覺 · 投球癖性與捕手動作差異辨識引擎 · 核心開發 Colby Morris"
  }
};

function getStoredLang() {
  return localStorage.getItem("preflight_lang") || "en";
}

function setLanguage(lang) {
  if (!PREFLIGHT_TRANSLATIONS[lang]) lang = "en";
  localStorage.setItem("preflight_lang", lang);

  const dict = PREFLIGHT_TRANSLATIONS[lang] || PREFLIGHT_TRANSLATIONS.en;

  // Update text nodes with data-i18n
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key] !== undefined) {
      el.textContent = dict[key];
    }
  });

  // Update HTML nodes with data-i18n-html
  document.querySelectorAll("[data-i18n-html]").forEach((el) => {
    const key = el.getAttribute("data-i18n-html");
    if (dict[key] !== undefined) {
      el.innerHTML = dict[key];
    }
  });

  // Update placeholders
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (dict[key] !== undefined) {
      el.setAttribute("placeholder", dict[key]);
    }
  });

  // Update active state on buttons
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    if (btn.getAttribute("data-lang") === lang) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  document.documentElement.lang = lang;
}

document.addEventListener("DOMContentLoaded", () => {
  const currentLang = getStoredLang();

  // Attach click listeners to language buttons
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const selected = btn.getAttribute("data-lang");
      setLanguage(selected);
    });
  });

  setLanguage(currentLang);
});

// Export for usage in window
window.PreflightI18n = {
  setLanguage,
  getStoredLang,
  translations: PREFLIGHT_TRANSLATIONS
};
