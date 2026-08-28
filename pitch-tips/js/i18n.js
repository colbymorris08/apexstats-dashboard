/**
 * Preflight Multi-Language Translation Engine
 * Authentic baseball terminology for English, Japanese (Katakana), Korean (KBO), Spanish, and Taiwanese (CPBL).
 */

const PREFLIGHT_TRANSLATIONS = {
  en: {
    lang_toolbar_label: "Language / 言語 / 언어 / Idioma / 語言:",
    brand_title: "Preflight",
    brand_sub: "Computer Vision · Lite Showcase",
    nav_overview: "Overview",
    nav_coverage: "Coverage Board",
    nav_leads: "Ranked Leads",
    nav_pricing: "Pricing & Access",
    nav_arch: "Architecture & CV",
    nav_request_pilot: "Request Pilot Access",

    hero_eyebrow: "Public Showcase · MLB & College Advance Scouting Intel",
    hero_h1: "Computer Vision \"Spot the Difference\" Engine for Pitch Tipping & Catcher Setup Cues.",
    hero_desc: "Preflight automates high-resolution landmark and bounding-box tracking to detect pitch-to-pitch mechanical variation—glove set height, forearm exposure, torso posture, hand depth, and catcher target positioning—strictly before ball release.",
    hero_btn_roupp: "Explore Showcase: Landen Roupp →",
    hero_btn_erod: "Eduardo Rodriguez →",
    hero_btn_webb: "Logan Webb →",
    hero_btn_schedule_audit: "Request Pilot / Schedule Scouting Audit →",

    meta_domain_label: "Domain",
    meta_domain_val: "Computer Vision Showcase",
    meta_pitchers_label: "Showcase Pitchers",
    meta_pitchers_val: "Landen Roupp, Eduardo Rodriguez, Webb",
    meta_catcher_label: "Showcase Catcher",
    meta_catcher_val: "Gabriel Moreno (ARI) Battery",
    meta_feed_label: "Baseline Feed",
    meta_feed_val: "Broadcast Center-Field (CF) & Synergy",
    meta_scope_label: "Detection Scope",
    meta_scope_val: "Glove, Posture, Forearm, Catcher Setup",
    meta_window_label: "Actionable Window",
    meta_window_val: "Set Position → Hand Break (0s Leakage)",

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
    catcher_cta_more: "Request Full NL West / College Opponent Catcher Scouting Audit →",

    showcase_eyebrow: "Interactive Showcase Dossiers",
    showcase_h2: "Unlocked Benchmark Mechanical Variance Leads",
    showcase_lede: "Examine top physical discrepancy leads and holdout-validated biomechanical metrics.",
    showcase_card_roupp_title: "Landen Roupp · SF Giants",
    showcase_card_roupp_badge: "UNLOCKED SHOWCASE",
    showcase_card_roupp_desc: "Changeup (CH) vs. Sinker (SI) delivery breakdown. Hand depth in glove (+0.238 torso lengths deeper on CH at lift) and glove rise offset.",
    showcase_card_roupp_btn: "View Mechanical Breakdown →",

    showcase_card_erod_title: "Eduardo Rodriguez · ARI D-backs",
    showcase_card_erod_badge: "UNLOCKED SHOWCASE",
    showcase_card_erod_desc: "Knee rise duration tempo (+11.3% predictive lift on CH vs FC across 40 scored fires) and glove speed variance on FF vs SI.",
    showcase_card_erod_btn: "View Mechanical Breakdown →",

    showcase_card_webb_title: "Logan Webb · SF Giants",
    showcase_card_webb_badge: "UNLOCKED SHOWCASE",
    showcase_card_webb_desc: "Changeup delivery speed into leg lift transition vs fastballs/sinkers and glove rise from set presentation.",
    showcase_card_webb_btn: "View Mechanical Breakdown →",

    roster_eyebrow: "Full League & Collegiate Coverage",
    roster_h2: "30+ Audited Arms & Full Rotation Pre-Series Database",
    roster_lede: "Complete division rotations, bullpens, and conference opponent audits available under Enterprise & Collegiate Pilots.",

    lock_banner_title: "🔒 Enterprise Scouting Database Lock",
    lock_banner_desc: "Access full 60+ arm MLB, NPB, KBO, CPBL, Mexico, Winter Leagues, and NCAA Division I team dossiers.",
    lock_banner_btn: "Request Enterprise Pilot Access →",

    modal_badge: "🔒 Confidential Scouting Pilot Request",
    modal_title: "Request Preflight Scouting Pilot & Access",
    modal_desc: "Inquire about 2027 College Licensing ($5k–$15k range), Conference Lockout Exclusivity ($18k–$35k range), or Pro Enterprise Deployments. A signed mutual NDA is executed prior to video sharing.",
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
    brand_sub: "コンピュータービジョン · ライト版ショーケース",
    nav_overview: "概要",
    nav_coverage: "球団カバレッジ",
    nav_leads: "動作差ランキング",
    nav_pricing: "料金プラン・独占権",
    nav_arch: "解析技術・CV",
    nav_request_pilot: "パイロット申請",

    hero_eyebrow: "公開ショーケース · プロ野球 (NPB/MLB) & 大学野球 高度スカウティング",
    hero_h1: "ピッチティッピング（投球癖）＆ キャッチャー構え検知 コンピュータービジョンAI",
    hero_desc: "Preflightは高精度な骨格ランドマークと物体検出ボックスを自動追跡し、グラブの高さ・前腕の露出・上体の傾き・手の深さ・キャッチャーのターゲット構えなど、ボールリリース前の微細な投球動作の違いを自動解析します。",
    hero_btn_roupp: "実例検証: ランデン・ループ投手 →",
    hero_btn_erod: "エドゥアルド・ロドリゲス投手 →",
    hero_btn_webb: "ローガン・ウェブ投手 →",
    hero_btn_schedule_audit: "パイロット申請・解析デモの予約 →",

    meta_domain_label: "ドメイン",
    meta_domain_val: "動作解析AI ショーケース",
    meta_pitchers_label: "検証投手",
    meta_pitchers_val: "ランデン・ループ, E.ロドリゲス, L.ウェブ",
    meta_catcher_label: "検証捕手",
    meta_catcher_val: "ガブリエル・モレノ (ARI) バッテリー",
    meta_feed_label: "基本映像",
    meta_feed_val: "バックスクリーンCFカメラ & Synergy映像",
    meta_scope_label: "検出対象",
    meta_scope_val: "グラブ, 姿勢, 前腕, キャッチャー構え",
    meta_window_label: "計測時間枠",
    meta_window_val: "セットポジション → ハンドブレイク (漏洩ゼロ)",

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

    showcase_eyebrow: "動作差異プロファイル",
    showcase_h2: "検証済み 投球動作差異ショーケース",
    showcase_lede: "トップ5の投球動作差異リードとホールドアウト検証済みの生体力学メトリクスを確認できます。",
    showcase_card_roupp_title: "ランデン・ループ · SFジャイアンツ",
    showcase_card_roupp_badge: "公開ショーケース",
    showcase_card_roupp_desc: "チェンジアップ (CH) と シンカー (SI) の動作分析。足上げ時のグラブ内での手の深さの差（チェンジアップで約0.238胴体比深い）とグラブ上昇差。",
    showcase_card_roupp_btn: "動作プロファイルを見る →",

    showcase_card_erod_title: "エドゥアルド・ロドリゲス · ARI",
    showcase_card_erod_badge: "公開ショーケース",
    showcase_card_erod_desc: "チェンジアップ対カットボールでの膝引き上げテンポ（40球検証で+11.3%の予測リフト）およびストレート対シンカーでのグラブ速度変化。",
    showcase_card_erod_btn: "動作プロファイルを見る →",

    showcase_card_webb_title: "ローガン・ウェブ · SFジャイアンツ",
    showcase_card_webb_badge: "公開ショーケース",
    showcase_card_webb_desc: "直球/シンカーに対するチェンジアップでの足上げ移行グラブ速度およびセット構えからのグラブ上昇幅。",
    showcase_card_webb_btn: "動作プロファイルを見る →",

    roster_eyebrow: "リーグ & 大学全域カバレッジ",
    roster_h2: "30名以上の解析済み投手 & 全ローテーション事前監査データベース",
    roster_lede: "球団・大学向けパイロット導入により、対戦相手全ローテーション、リリーフ陣、捕手の事前スカウティングが利用可能です。",

    lock_banner_title: "🔒 エンタープライズ専売データベース ロック",
    lock_banner_desc: "MLB、NPB（日本プロ野球）、KBO（韓国）、CPBL（台湾）、メキシカンリーグ、ウィンターリーグ、NCAA大学野球の完全データベース。",
    lock_banner_btn: "パイロット利用・独占契約の申請 →",

    modal_badge: "🔒 守秘義務契約 (NDA) パイロット申請",
    modal_title: "Preflight パイロット導入・個別相談申請",
    modal_desc: "2027年大学野球ライセンス（5,000〜15,000ドル）、リーグ内独占契約（18,000〜35,000ドル）、プロ球団向けエンタープライズ導入のご相談。映像提供前に相互NDA（秘密保持契約）を締結します。",
    modal_lbl_name: "氏名・役職 *",
    modal_lbl_org: "所属球団 / 大学名 *",
    modal_lbl_email: "公式メールアドレス *",
    modal_lbl_level: "所属リーグ / レベル *",
    modal_lbl_tier: "希望プラン・独占権 *",
    modal_lbl_notes: "ご要望 / 対象対戦相手 / 映像連携形式",
    modal_submit: "パイロット申請を送信 →",
    modal_direct_email: "直接メールで問い合わせ",
    modal_success_title: "パイロット申請を受け付けました。",
    modal_success_body: "Colby Morris (colby.morris08@gmail.com) 宛てのメール作成画面が開きます。秘密保持契約（NDA）の締結および映像連携について速やかにご連絡いたします。",

    footer_text: "Preflight コンピュータービジョン · 動作検証から実戦導入へ · 開発: Colby Morris"
  },

  ko: {
    lang_toolbar_label: "언어 / Language:",
    brand_title: "Preflight",
    brand_sub: "컴퓨터 비전 · 라이트 쇼케이스",
    nav_overview: "개요",
    nav_coverage: "구단 커버리지",
    nav_leads: "투구폼 버릇 랭킹",
    nav_pricing: "도입 요금·독점권",
    nav_arch: "분석 기술·CV",
    nav_request_pilot: "파일럿 신청",

    hero_eyebrow: "공개 쇼케이스 · KBO/MLB 프로 및 대학야구 첨단 전력분석",
    hero_h1: "투구 폼 버릇(피칭 팁) 및 포수 셋업 감지 컴퓨터 비전 AI 엔진",
    hero_desc: "Preflight는 고해상도 랜드마크와 바운딩 박스를 자동 추적하여 글러브 셋 높이, 전완 노출, 상체 각도, 손 깊이, 포수의 타깃 위치 등 투구 릴리스 전의 미세한 동작 차이를 자동으로 정밀 분석합니다.",
    hero_btn_roupp: "실증 분석: 랜든 룹 투수 →",
    hero_btn_erod: "에두아르도 로드리게스 투수 →",
    hero_btn_webb: "로건 웹 투수 →",
    hero_btn_schedule_audit: "파일럿 신청 및 전력분석 데모 예약 →",

    meta_domain_label: "도메인",
    meta_domain_val: "동작 분석 AI 쇼케이스",
    meta_pitchers_label: "검증 투수",
    meta_pitchers_val: "랜든 룹, E.로드리게스, L.웹",
    meta_catcher_label: "검증 포수",
    meta_catcher_val: "가브리엘 모레노 (ARI) 배터리",
    meta_feed_label: "기본 영상",
    meta_feed_val: "중계 센터필드(CF) 카메라 & Synergy 영상",
    meta_scope_label: "감지 영역",
    meta_scope_val: "글러브, 투구자세, 전완, 포수 셋업",
    meta_window_label: "측정 시간구간",
    meta_window_val: "세트 포지션 → 핸드 브레이크 (정보유출 0초)",

    workflow_eyebrow: "현장 전력분석 4단계 프로세스",
    workflow_h2: "AI 동작 감지부터 타석에서의 실전 공략까지",
    workflow_lede: "프로 구단 및 대학 야구팀이 AI 투구폼 차이 분석을 실전 승리로 연결하는 운영 방식.",
    step1_num: "1단계",
    step1_title: "AI 모델의 투구 패턴 자동 감지",
    step1_desc: "Preflight가 Synergy 및 경기 영상을 자동 분석하여 30개 이상의 생체역학 랜드마크를 추적하고 구종별 물리적 동작 차이를 찾아냅니다.",
    step2_num: "2단계",
    step2_title: "전력분석원의 투구 버릇 검증",
    step2_desc: "데이터 분석팀이 구종 배분, 순열 검정, 다경기 홀드아웃 교차검증을 거쳐 단순 우연을 배제하고 유의미한 예측력을 확인합니다.",
    step3_num: "3단계",
    step3_title: "코칭스태프의 타자 시각 지도",
    step3_desc: "타격 코치가 검증된 투구폼 버릇(글러브 위치, 킥 템포, 포수 미트 높이)을 카운트별 노림수 전략으로 타자들에게 전달합니다.",
    step4_num: "4단계",
    step4_title: "선수들의 그라운드 실전 실행",
    step4_desc: "타석의 타자와 2루 주자가 테이크백 전 동작에서 구종을 미리 파악하여 노림수를 좁히고 결정적인 타격 우위를 점합니다.",

    catcher_eyebrow: "실전 배터리 전력분석 케이스",
    catcher_h2: "포수 사전 셋업 및 미트 타깃 위치 버릇 감지",
    catcher_lede: "투수만 투구폼을 흘리는 것이 아닙니다. Preflight는 투구 동작 시작 전 포수의 스탠스 폭, 타깃 미트 높이, 정지 타이밍을 추적합니다.",
    catcher_moreno_title: "가브리엘 모레노 (ARI · 포수)",
    catcher_moreno_sub: "투구 전 미트 타깃 높이 변화 및 셋업 정지 타이밍 (배터리 분석)",
    catcher_stat1_lbl: "신호 분리도",
    catcher_stat2_lbl: "미트 높이 차이",
    catcher_stat3_lbl: "구종 판별률",
    catcher_stat4_lbl: "시간적 정보누출",
    catcher_cue1_title: "1. 투구 전 미트 타깃 높이 편차 (패스트볼 vs 체인지업/슬라이더):",
    catcher_cue1_desc: "포심 패스트볼 시 모레노 포수는 미트를 3.4인치 높게 셋업합니다. 반면 체인지업과 슬라이더 시에는 더 깊게 웅크리며 낮게 타깃을 형성합니다.",
    catcher_cue2_title: "2. 레그킥 전 포수 자세 정지 타이밍 차이:",
    catcher_cue2_desc: "변화구 구종 시 모레노 포수는 패스트볼 대비 210ms 일찍 미트를 완전 정지시켜 2루 주자와 벤치에 사전 힌트를 노출합니다.",
    catcher_cta_more: "상대팀 포수 셋업 및 배터리 전력분석 리포트 요청 →",

    showcase_eyebrow: "투구 동작 프로파일",
    showcase_h2: "검증된 투구폼 물리적 차이 쇼케이스",
    showcase_lede: "상위 5개 동작 차이 리드와 홀드아웃 검증된 생체역학 메트릭을 확인할 수 있습니다.",
    showcase_card_roupp_title: "랜든 룹 · SF 자이언츠",
    showcase_card_roupp_badge: "공개 쇼케이스",
    showcase_card_roupp_desc: "체인지업(CH) vs 싱커(SI) 투구폼 분석. 레그킥 시 글러브 내 손 깊이 차이(체인지업 시 약 0.238 몸통비율 깊음) 및 글러브 상승량 차이.",
    showcase_card_roupp_btn: "동작 프로파일 보기 →",

    showcase_card_erod_title: "에두아르도 로드리게스 · ARI",
    showcase_card_erod_badge: "공개 쇼케이스",
    showcase_card_erod_desc: "체인지업 vs 커터 시 무릎 인양 템포(40구 검증 기준 +11.3% 예측 리프트) 및 패스트볼 vs 싱커 글러브 속도 편차.",
    showcase_card_erod_btn: "동작 프로파일 보기 →",

    showcase_card_webb_title: "로건 웹 · SF 자이언츠",
    showcase_card_webb_badge: "공개 쇼케이스",
    showcase_card_webb_desc: "직구/싱커 대비 체인지업 시 레그킥 전환 글러브 속도 및 셋업 자세 글러브 상승량.",
    showcase_card_webb_btn: "동작 프로파일 보기 →",

    roster_eyebrow: "리그 및 대학 전체 커버리지",
    roster_h2: "30인 이상 분석 완료 투수 및 전체 로테이션 사전분석 DB",
    roster_lede: "구단 및 대학 팀용 엔터프라이즈 파일럿을 통해 상대팀 전원 로테이션, 불펜, 포수 전력분석 데이터가 제공됩니다.",

    lock_banner_title: "🔒 엔터프라이즈 전용 데이터베이스 잠금",
    lock_banner_desc: "KBO, MLB, NPB, CPBL, 멕시코리그, 윈터리그 및 NCAA 대학야구 전체 팀 분석 데이터.",
    lock_banner_btn: "파일럿 도입 및 전력분석 신청 →",

    modal_badge: "🔒 비밀유지계약(NDA) 파일럿 신청",
    modal_title: "Preflight 전력분석 파일럿 도입 신청",
    modal_desc: "2027 시즌 대학 라이선스($5,000~$15,000), 리그 내 독점권($18,000~$35,000), 프로 구단 엔터프라이즈 도입 문의. 영상 전달 전 상호 비밀유지계약(NDA)을 체결합니다.",
    modal_lbl_name: "성명 및 직책 *",
    modal_lbl_org: "소속 구단 / 대학명 *",
    modal_lbl_email: "공식 이메일 *",
    modal_lbl_level: "소속 리그 / 레벨 *",
    modal_lbl_tier: "희망 플랜 및 독점권 *",
    modal_lbl_notes: "요청사항 / 분석 희망 상대팀 / 영상 연동 방식",
    modal_submit: "파일럿 신청 제출 →",
    modal_direct_email: "직접 이메일 문의",
    modal_success_title: "파일럿 신청이 접수되었습니다.",
    modal_success_body: "Colby Morris (colby.morris08@gmail.com) 앞으로 이메일 작성창이 준비되었습니다. 비밀유지계약(NDA) 체결 및 영상 연동을 위해 신속히 회신드리겠습니다.",

    footer_text: "Preflight 컴퓨터 비전 · 전력분석 검증에서 실전 도입까지 · 개발: Colby Morris"
  },

  es: {
    lang_toolbar_label: "Idioma / Language:",
    brand_title: "Preflight",
    brand_sub: "Visión por Computadora · Muestra Lite",
    nav_overview: "Resumen",
    nav_coverage: "Tablero de Cobertura",
    nav_leads: "Patrones Detectados",
    nav_pricing: "Precios y Exclusividad",
    nav_arch: "Arquitectura y CV",
    nav_request_pilot: "Solicitar Acceso Piloto",

    hero_eyebrow: "Muestra Pública · Inteligencia de Avanzada para MLB, Ligas Invernales y Béisbol Colegial",
    hero_h1: "Motor de Visión por Computadora para Detección de Inclinación de Lanzamientos (Tipping) y Postura del Receptor.",
    hero_desc: "Preflight automatiza el rastreo de alta resolución de puntos anatómicos y cuadros delimitadores para detectar variaciones mecánicas lanzamiento a lanzamiento (altura del guante, postura del torso, profundidad de la mano y ubicación del receptor) estrictamente antes de soltar la pelota.",
    hero_btn_roupp: "Explorar Muestra: Landen Roupp →",
    hero_btn_erod: "Eduardo Rodríguez →",
    hero_btn_webb: "Logan Webb →",
    hero_btn_schedule_audit: "Solicitar Prueba Piloto / Auditoría →",

    meta_domain_label: "Dominio",
    meta_domain_val: "Visión por Computadora",
    meta_pitchers_label: "Lanzadores en Muestra",
    meta_pitchers_val: "Landen Roupp, Eduardo Rodríguez, Webb",
    meta_catcher_label: "Receptor en Muestra",
    meta_catcher_val: "Batería de Gabriel Moreno (ARI)",
    meta_feed_label: "Toma Base",
    meta_feed_val: "Cámara Center-Field (CF) y Synergy",
    meta_scope_label: "Alcance",
    meta_scope_val: "Guante, Postura, Antebrazo, Receptor",
    meta_window_label: "Ventana de Acción",
    meta_window_val: "Posición de Set → Ruptura de Manos (0s Fuga)",

    workflow_eyebrow: "El Proceso Operativo de 4 Pasos",
    workflow_h2: "De la Detección por IA a la Ejecución en la Caja de Bateo",
    workflow_lede: "Cómo los programas colegiales y las franquicias profesionales convierten la detección de patrones en victorias en el terreno de juego.",
    step1_num: "PASO 01",
    step1_title: "El Modelo Encuentra el Patrón",
    step1_desc: "Preflight procesa automáticamente videos de Synergy y tomas de estadio, rastreando más de 30 puntos biomecánicos para aislar diferencias entre lanzamientos.",
    step2_num: "PASO 02",
    step2_title: "Los Analistas Confirman el Detalle",
    step2_desc: "Los scouts de avanzada y analistas validan la variación contra la mezcla de pitcheo y pruebas estadísticas para descartar el azar.",
    step3_num: "PASO 03",
    step3_title: "Los Coaches Enseñan el Reconocimiento",
    step3_desc: "El cuerpo técnico traduce los detalles mecánicos en señales visuales claras (altura del guante, tempo de elevación, altura del receptor) para los bateadores.",
    step4_num: "PASO 04",
    step4_title: "Los Jugadores Ejecutan en el Terreno",
    step4_desc: "Los bateadores y corredores en segunda base reconocen el lanzamiento antes de la aceleración del brazo, anticipando el pitcheo en conteos clave.",

    catcher_eyebrow: "Inteligencia de Avanzada en Baterías",
    catcher_h2: "Patrones de Postura y Ubicación de la Mascota del Receptor",
    catcher_lede: "Los detalles no provienen solo del lanzador. Preflight rastrea la amplitud de piernas, altura del guante y tiempo de quietud del receptor.",
    catcher_moreno_title: "Gabriel Moreno (ARI Diamondbacks · Receptor)",
    catcher_moreno_sub: "Altura de la Mascota Pre-Lanzamiento y Tiempo de Quietud en la Sentadilla",
    catcher_stat1_lbl: "Separación de Señal",
    catcher_stat2_lbl: "Variación de Altura",
    catcher_stat3_lbl: "Tasa de Discriminación",
    catcher_stat4_lbl: "Fuga Temporal",
    catcher_cue1_title: "1. Altura de la Mascota Pre-Lanzamiento (Recta vs. Cambio/Slider):",
    catcher_cue1_desc: "En rectas de cuatro costuras, Moreno coloca el guante 3.4 pulgadas más alto. En cambios y sliders, se agacha más profundo y coloca la mascota baja.",
    catcher_cue2_title: "2. Tiempo de Quietud de la Sentadilla Previo a la Elevación:",
    catcher_cue2_desc: "En lanzamientos rompientes y lentos, Moreno logra la quietud del guante 210ms antes que en rectas, dando a corredores y coaches un aviso previo claro.",
    catcher_cta_more: "Solicitar Auditoría Completa de Receptores Rivales →",

    showcase_eyebrow: "Muestras de Patrones Mecánicos",
    showcase_h2: "Patrones Mecánicos Verificados",
    showcase_lede: "Inspeccione los principales indicadores físicos e indicadores biomecánicos validados por holdout.",
    showcase_card_roupp_title: "Landen Roupp · SF Giants",
    showcase_card_roupp_badge: "MUESTRA DESBLOQUEADA",
    showcase_card_roupp_desc: "Análisis de Cambio (CH) vs Sinker (SI). Profundidad de la mano en el guante (+0.238 torsos más profunda en CH al levantar la pierna) y elevación del guante.",
    showcase_card_roupp_btn: "Ver Perfil de Lanzamiento →",

    showcase_card_erod_title: "Eduardo Rodríguez · ARI D-backs",
    showcase_card_erod_badge: "MUESTRA DESBLOQUEADA",
    showcase_card_erod_desc: "Tempo de elevación de rodilla (+11.3% de ventaja predictiva en Cambio vs Cutter en 40 lanzamientos) y velocidad de guante en Recta vs Sinker.",
    showcase_card_erod_btn: "Ver Perfil de Lanzamiento →",

    showcase_card_webb_title: "Logan Webb · SF Giants",
    showcase_card_webb_badge: "MUESTRA DESBLOQUEADA",
    showcase_card_webb_desc: "Velocidad del guante hacia la elevación de pierna en Cambios vs Rectas/Sinkers y ascenso del guante desde la posición de set.",
    showcase_card_webb_btn: "Ver Perfil de Lanzamiento →",

    roster_eyebrow: "Cobertura Completa",
    roster_h2: "Más de 30 Brazos Auditados y Base de Datos Completa",
    roster_lede: "Rotaciones completas, bullpens y auditorías de rivales disponibles bajo programas piloto.",

    lock_banner_title: "🔒 Bloqueo de Base de Datos Enterprise",
    lock_banner_desc: "Acceda a la base de datos completa de MLB, NPB, KBO, CPBL, México (LMB), Ligas Invernales (LIDOM, LMP, LVBP) y NCAA.",
    lock_banner_btn: "Solicitar Acceso Piloto Enterprise →",

    modal_badge: "🔒 Solicitud de Piloto Confidencial con NDA",
    modal_title: "Solicitar Prueba Piloto y Acceso a Preflight",
    modal_desc: "Consulte sobre licencias colegiales 2027 ($5k–$15k), exclusividad de conferencia ($18k–$35k) o implementaciones profesionales. Se firma un acuerdo de confidencialidad (NDA) antes de compartir video.",
    modal_lbl_name: "Nombre Completo *",
    modal_lbl_org: "Organización / Universidad *",
    modal_lbl_email: "Correo Electrónico Oficial *",
    modal_lbl_level: "Nivel / División *",
    modal_lbl_tier: "Nivel de Interés *",
    modal_lbl_notes: "Notas / Rivales Específicos / Plazos",
    modal_submit: "Enviar Solicitud Piloto →",
    modal_direct_email: "Correo Directo",
    modal_success_title: "Gracias por su solicitud.",
    modal_success_body: "Se ha preparado su cliente de correo con los detalles dirigidos a Colby Morris (colby.morris08@gmail.com). Responderemos de inmediato para coordinar el NDA y la integración de video.",

    footer_text: "Preflight Visión por Computadora · De la Prueba de Concepto al Despliegue en Vivo · Desarrollado por Colby Morris"
  },

  "zh-TW": {
    lang_toolbar_label: "語言 / Language:",
    brand_title: "Preflight",
    brand_sub: "電腦視覺 · 精選體驗版 (Lite)",
    nav_overview: "總覽",
    nav_coverage: "球隊監控表",
    nav_leads: "動作差異排名",
    nav_pricing: "方案與獨家權",
    nav_arch: "視覺技術・CV",
    nav_request_pilot: "申請測試試用",

    hero_eyebrow: "公開體驗版 · 職棒 (CPBL/MLB/NPB/KBO) 與大專棒球先進情蒐",
    hero_h1: "自動抓投球小動作（投球習慣破解）與捕手蹲捕站位 電腦視覺 AI 引擎",
    hero_desc: "Preflight 透過高解析度關節節點與物件框自動追蹤，在投手投球出手前，精準辨識各球種間的手套位置高度、前臂露出、軀幹傾斜、手套內部握球深度以及捕手接球目標站位等細微動作差異。",
    hero_btn_roupp: "實例分析：Landen Roupp 投手 →",
    hero_btn_erod: "Eduardo Rodriguez 投手 →",
    hero_btn_webb: "Logan Webb 投手 →",
    hero_btn_schedule_audit: "申請試用／預約情蒐分析演示 →",

    meta_domain_label: "應用領域",
    meta_domain_val: "電腦視覺動作分析",
    meta_pitchers_label: "展示投手",
    meta_pitchers_val: "Landen Roupp, E. Rodriguez, Logan Webb",
    meta_catcher_label: "展示捕手",
    meta_catcher_val: "Gabriel Moreno (ARI) 投捕搭檔",
    meta_feed_label: "基礎影像",
    meta_feed_val: "中外野轉播視角 (CF) 與 Synergy 影片",
    meta_scope_label: "偵測項目",
    meta_scope_val: "手套高度、站姿、前臂、捕手站位",
    meta_window_label: "量測區間",
    meta_window_val: "固定準備動作 (Set) → 雙手分開 (0秒洩漏)",

    workflow_eyebrow: "實戰情蒐導入四步驟",
    workflow_h2: "從 AI 動作偵測到打擊區實戰破解",
    workflow_lede: "職棒球團與大專球隊如何將電腦視覺動作差異轉化為球場上的勝場。",
    step1_num: "步驟 01",
    step1_title: "AI 演算法自動偵測投球慣性",
    step1_desc: "Preflight 自動匯入 Synergy 或球場影像，追蹤超過 30 個生物力學骨架節點，自動分離各球種間的物理動作差異。",
    step2_num: "步驟 02",
    step2_title: "情蒐分析師驗證真實性",
    step2_desc: "數據分析師比對球種配球比例、排列檢定與跨場次交叉驗證，排除隨機誤差，確認真正具備預測價值的動作小細節。",
    step3_num: "步驟 03",
    step3_title: "教練團轉化為打者視覺指標",
    step3_desc: "打擊教練將經確認的動作小習慣（手套高度、抬腿節奏、捕手目標高低）整理為好球數特定策略，指導打者提前預判。",
    step4_num: "步驟 04",
    step4_title: "打者與跑者在場上精準執行",
    step4_desc: "打擊區內的打者與二壘跑者在投手揮臂啟動前即辨識球種，鎖定特定球種進行攻擊，奪得壓倒性優勢。",

    catcher_eyebrow: "投捕搭配實戰情蒐案例",
    catcher_h2: "捕手準備動作與手套預設目標位置小動作",
    catcher_lede: "小動作不只來自投手。Preflight 亦同步追蹤捕手的蹲捕寬度、手套預設高度與身體靜止時間點。",
    catcher_moreno_title: "Gabriel Moreno (ARI響尾蛇 · 捕手)",
    catcher_moreno_sub: "投球前手套目標高度差異與蹲捕靜止時間點分析",
    catcher_stat1_lbl: "訊號分離度",
    catcher_stat2_lbl: "手套目標高度差",
    catcher_stat3_lbl: "球種判別率",
    catcher_stat4_lbl: "時間洩漏",
    catcher_cue1_title: "1. 投球前手套目標高度偏差（四縫線快速球 vs 變速球/滑球）：",
    catcher_cue1_desc: "投四縫線快速球時，Moreno 捕手手套靜止位置高出 3.4 英吋；投變速球與滑球時則蹲得更深並將手套預先放低。",
    catcher_cue2_title: "2. 投手抬腿前捕手身體靜止時間點差異：",
    catcher_cue2_desc: "投變化球時，Moreno 捕手比投快速球時提早 210 毫秒完全靜止手套，為二壘跑者與休息區提供明確的預判訊號。",
    catcher_cta_more: "申請對手捕手與投捕搭檔情蒐分析 →",

    showcase_eyebrow: "動作差異特徵",
    showcase_h2: "已驗證投球物理動作差異展示",
    showcase_lede: "檢視前五大關鍵物理差異特徵與交叉驗證之生物力學指標。",
    showcase_card_roupp_title: "Landen Roupp · 舊金山巨人",
    showcase_card_roupp_badge: "已解鎖展示",
    showcase_card_roupp_desc: "變速球 (CH) 與 伸卡球 (SI) 動作分析。抬腿時手在手套深處的差異（變速球時深約 0.238 軀幹長度）與手套上升幅度差異。",
    showcase_card_roupp_btn: "檢視動作特徵拆解 →",

    showcase_card_erod_title: "Eduardo Rodriguez · 亞利桑那響尾蛇",
    showcase_card_erod_badge: "已解鎖展示",
    showcase_card_erod_desc: "變速球對卡特球的抬膝啟動節奏（經 40 球驗證具 +11.3% 預測提升）及快速球對伸卡球的手套速度變異。",
    showcase_card_erod_btn: "檢視動作特徵拆解 →",

    showcase_card_webb_title: "Logan Webb · 舊金山巨人",
    showcase_card_webb_badge: "已解鎖展示",
    showcase_card_webb_desc: "變速球相較於快速球/伸卡球在抬腿轉換時的手套速度及從準備動作開始的手套上升幅度。",
    showcase_card_webb_btn: "檢視動作特徵拆解 →",

    roster_eyebrow: "全聯盟與大專球隊涵蓋範圍",
    roster_h2: "超過 30 位已分析投手及全輪值賽前情蒐資料庫",
    roster_lede: "球團與學校測試導入後可獲取對手全先發輪值、牛棚投手與捕手之完整情蒐報告。",

    lock_banner_title: "🔒 企業專屬完整資料庫鎖定",
    lock_banner_desc: "涵蓋中華職棒 (CPBL)、MLB、日本職棒 (NPB)、韓國職棒 (KBO)、墨西哥聯盟、冬季聯盟及 NCAA 大學棒球完整資料庫。",
    lock_banner_btn: "申請企業／球團試用權限 →",

    modal_badge: "🔒 保密協議 (NDA) 試用申請",
    modal_title: "申請 Preflight 情蒐試用與權限",
    modal_desc: "洽詢 2027 賽季大專授權方案（5,000～15,000 美元）、分區獨家買斷權（18,000～35,000 美元）或職業球團企業方案。提供影片前均會先簽署雙方保密協議 (NDA)。",
    modal_lbl_name: "姓名與職稱 *",
    modal_lbl_org: "所屬球團／學校名稱 *",
    modal_lbl_email: "官方電子信箱 *",
    modal_lbl_level: "所屬聯盟／層級 *",
    modal_lbl_tier: "欲洽詢方案或獨家權 *",
    modal_lbl_notes: "備註／欲分析之特定對手／影片形式",
    modal_submit: "送出試用申請 →",
    modal_direct_email: "直接發送信件",
    modal_success_title: "已收到您的試用申請。",
    modal_success_body: "系統已為您準備好致 Colby Morris (colby.morris08@gmail.com) 的信件內容。我們將儘速與您聯繫簽署保密協議 (NDA) 及影像串接事宜。",

    footer_text: "Preflight 電腦視覺 · 從概念驗證到實戰部署 · 開發者：Colby Morris"
  }
};

function getStoredLang() {
  const saved = localStorage.getItem("preflight_lang");
  if (saved && PREFLIGHT_TRANSLATIONS[saved]) return saved;
  const navLang = (navigator.language || navigator.userLanguage || "en").toLowerCase();
  if (navLang.startsWith("ja")) return "ja";
  if (navLang.startsWith("ko")) return "ko";
  if (navLang.startsWith("es")) return "es";
  if (navLang.startsWith("zh")) return "zh-TW";
  return "en";
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
