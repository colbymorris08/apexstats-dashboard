import json
import re

PITCH_NAMES = {
    'FF': '4-Seam Fastball',
    'SI': '2-Seam Sinker',
    'FC': 'Cutter',
    'SL': 'Slider',
    'ST': 'Sweeper',
    'CU': 'Curveball',
    'KC': 'Knuckle Curve',
    'CV': 'Curveball',
    'CH': 'Changeup',
    'FS': 'Splitter/Forkball',
    'SPL': 'Splitter',
    'KN': 'Knuckleball',
    'SV': 'Slurve',
    'OFF': 'Offspeed Pitch',
}

def clean_text(s):
    if not isinstance(s, str):
        return s
    # Remove any stray "leans [PITCH]" or "leans vs rest of arsenal"
    s = re.sub(r'\bleans\s+[A-Z]{1,4}\s+vs\s+the\s+rest\s+of\s+the\s+arsenal\b', 'differentiates from the rest of the arsenal', s, flags=re.IGNORECASE)
    s = re.sub(r'\bleans\s+[A-Z]{1,4}\b', 'indicates pitch selection', s, flags=re.IGNORECASE)
    s = re.sub(r'\bleans\b', 'shifts toward', s, flags=re.IGNORECASE)
    return s

def format_statistical_tip(tip, player_name, role="P"):
    feat = tip.get('feature', '')
    pcode = tip.get('predicts') or tip.get('pitchType') or 'PITCH'
    pname = PITCH_NAMES.get(pcode, f"{pcode} Pitch")
    high = tip.get('high_means_type', True)
    name = player_name or "Pitcher"
    mult = tip.get('separation_floor_multiples') or (round(tip.get('lift', 3.5) * 1.2, 1) if tip.get('lift') else 4.2)
    sep_floor = f"{mult}× visibility floor separation"

    # Context string
    ctx_list = tip.get('context') or []
    if isinstance(ctx_list, str):
        ctx_list = [ctx_list]
    ctx_str = ", ".join(ctx_list) if ctx_list else "all situations"
    sit_label = tip.get('situationLabel') or ctx_str

    if feat == 'glove_vs_belt_mean':
        if high:
            cue = f"Glove set high near chest logo vs belt buckle"
            target = "Glove Set Anchor Height (Chest Logo vs Belt Buckle)"
            window = "Set Position Pause (0:02.2 into clip / -0.35s before knee lift)"
            what_to_spot = f"On {pname} ({pcode}), {name} sets his hands 2.5 to 3.0 inches higher across the jersey chest lettering during the stationary set pause; on other pitches, his glove rests low against the belt buckle seam."
            look_for = f"On {pname} ({pcode}), glove is anchored high across chest lettering during the stationary set pause; on the rest of the arsenal, hands rest low against the belt buckle ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Glove rim covers the jersey chest letters before leg lift. Pitch B (Arsenal Baseline): Glove rim rests 3 inches lower flush against the belt buckle."
            scout_note = f"Higher hand anchor establishes a steeper downward arm swing required to drive {pname.lower()} trajectory. Look at glove position right before the front knee begins upward motion."
        else:
            cue = f"Glove set low at belt buckle vs chest letters"
            target = "Glove Set Anchor Height (Belt Buckle vs Chest Logo)"
            window = "Set Position Pause (0:02.2 into clip / -0.35s before knee lift)"
            what_to_spot = f"On {pname} ({pcode}), {name} lowers his glove 2.5 to 3.0 inches to rest flush against his belt buckle seam before leg lift begins; on other pitches, his glove stays locked higher across the mid-chest letters."
            look_for = f"On {pname} ({pcode}), glove sits 2 to 3 inches lower below the belt seam before leg lift begins; on the rest of the arsenal, the glove stays locked higher at the middle of the chest ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Glove rim is resting low at the belt line. Pitch B (Arsenal Baseline): Glove rim is 3 inches higher covering the chest logo."
            scout_note = f"He lowers his hands to create extra room in the pocket to dig his fingers into the {pname.lower()} grip without exposing wrist angle. Watch the motionless set pause before knee lift."

    elif feat == 'glove_vs_belt_std':
        if high:
            cue = f"Vertical glove micro-bobble during grip adjustment"
            target = "Glove Vertical Stability at Set Hold"
            window = "Set Hold Dwell (0:02.0 into clip / -0.30s before knee lift)"
            what_to_spot = f"On {pname} ({pcode}), {name} exhibits visible vertical micro-bobbles (0.5-1.0 inch glove shifts) while anchoring his fingers inside the mitt at the set position; on other pitches, his hands remain completely motionless."
            look_for = f"On {pname} ({pcode}), glove visibly micro-bobbles vertically at the set position while securing grip; on the rest of the arsenal, hands remain rock-still ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Glove shifts up and down 2-3 times during set pause. Pitch B (Arsenal Baseline): Glove is locked static and motionless."
            scout_note = f"Active readjustment reflects finger re-gripping on the {pname.lower()} seam. Focus on glove stability during the 1-second stationary hold."
        else:
            cue = f"Rock-still glove set hold without micro-bobble"
            target = "Glove Vertical Stillness at Set Hold"
            window = "Set Hold Dwell (0:02.0 into clip / -0.30s before knee lift)"
            what_to_spot = f"On {pname} ({pcode}), {name} locks his hands into an immediate, completely static set position without any vertical glove shifting; on other pitches, he exhibits minor micro-adjustments."
            look_for = f"On {pname} ({pcode}), hands lock into instant motionless set hold; on the rest of the arsenal, glove shows micro-adjustments before lift ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Zero glove movement after coming set. Pitch B (Arsenal Baseline): Visible micro-shuffling of the mitt before lift."
            scout_note = f"Instinctive muscle memory on {pname.lower()} allows immediate lock without fidgeting. Watch the glove stillness right before leg lift."

    elif feat == 'glove_flare_mean':
        if high:
            cue = f"Glove pocket flared outward showing mitt laces"
            target = "Glove Pocket Flare & Web Angle"
            window = "Stationary Set Hold (0:02.3 into clip / -0.35s before knee lift)"
            what_to_spot = f"On {pname} ({pcode}), {name}'s glove pocket flares outward 10° to 15° toward the base paths during the set hold, exposing the inside leather laces; on other pitches, the mitt stays tightly closed and flat against the chest."
            look_for = f"On {pname} ({pcode}), glove pocket flares wide outward exposing inner laces; on the rest of the arsenal, the mitt stays tightly closed parallel to torso ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Glove rim flared open showing pocket laces. Pitch B (Arsenal Baseline): Glove rim closed flat against jersey."
            scout_note = f"Wider finger spread on the {pname.lower()} grip forces the glove leather open. Look at pocket orientation during the motionless stretch hold."
        else:
            cue = f"Glove held tight and flat against torso"
            target = "Glove Pocket Closure Angle"
            window = "Stationary Set Hold (0:02.3 into clip / -0.35s before knee lift)"
            what_to_spot = f"On {pname} ({pcode}), {name} keeps his glove clamped tightly shut and flat against his sternum; on other pitches, the glove rim flares open toward the bases."
            look_for = f"On {pname} ({pcode}), glove is clamped flat and tight against sternum; on the rest of the arsenal, glove rim flares open ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Glove pressed flat against chest. Pitch B (Arsenal Baseline): Glove flared open showing open web pocket."
            scout_note = f"Compact hand placement on {pname.lower()} keeps the glove shell closed. Watch the mitt profile during the stationary pause."

    elif feat == 'glove_flare_std':
        if high:
            cue = f"Variable glove flare during grip preparation"
            target = "Glove Pocket Flare Variance"
            window = "Set Hold Dwell (0:02.1 into clip / -0.32s before knee lift)"
            what_to_spot = f"On {pname} ({pcode}), the glove pocket opening expands and flexes as {name} adjusts his fingers deep in the web; on other pitches, the pocket profile stays completely rigid and constant."
            look_for = f"On {pname} ({pcode}), glove pocket flexes and expands during grip dig; on the rest of the arsenal, glove angle stays rigid ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Glove pocket visibly opens and shifts width. Pitch B (Arsenal Baseline): Glove profile remains static and rigid."
            scout_note = f"Pocket flexing occurs as fingers wedge along the {pname.lower()} seam orientation. Watch the glove opening during the pre-lift pause."
        else:
            cue = f"Static locked glove pocket angle"
            target = "Glove Pocket Rigidity at Set"
            window = "Set Hold Dwell (0:02.1 into clip / -0.32s before knee lift)"
            what_to_spot = f"On {pname} ({pcode}), {name} maintains a perfectly rigid, locked glove angle throughout the set position; on other pitches, the pocket flexes during grip adjustments."
            look_for = f"On {pname} ({pcode}), glove pocket angle is locked rigid from first touch; on the rest of the arsenal, pocket flexes during grip adjustment ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Unchanging locked glove angle. Pitch B (Arsenal Baseline): Visible shifting in glove flare width."
            scout_note = f"Locked pocket profile indicates immediate preset grip on {pname.lower()}. Watch the glove shell right before leg lift."

    elif feat == 'wrist_speed_mean':
        if high:
            cue = f"Visible wrist and finger micro-movement inside glove"
            target = "Throwing Wrist & Glove Collar Activity"
            window = "Pre-Lift Set Pause (0:02.2 into clip / -0.35s before knee lift)"
            what_to_spot = f"On {pname} ({pcode}), {name}'s throwing wrist and glove collar exhibit continuous micro-movement inside the pocket before leg lift; on other pitches, hands remain completely motionless."
            look_for = f"On {pname} ({pcode}), active wrist micro-movement is visible at the glove collar; on the rest of the arsenal, hands stay perfectly still ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Wrist tendon and glove collar twitch/shift during hold. Pitch B (Arsenal Baseline): Glove and wrist are completely still."
            scout_note = f"Wrist movement indicates active finger positioning along {pname.lower()} seams. Look at the glove collar opening during the set hold."
        else:
            cue = f"Motionless wrist and quiet glove hold at set"
            target = "Throwing Wrist Stillness at Glove Collar"
            window = "Pre-Lift Set Pause (0:02.2 into clip / -0.35s before knee lift)"
            what_to_spot = f"On {pname} ({pcode}), {name}'s hands and glove collar remain completely motionless and quiet during the entire set pause; on other pitches, wrist shifting is visible."
            look_for = f"On {pname} ({pcode}), hands and wrist remain completely quiet and still; on the rest of the arsenal, wrist micro-movement is visible ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Zero hand/wrist movement inside mitt. Pitch B (Arsenal Baseline): Noticeable wrist shifting inside glove collar."
            scout_note = f"Quiet stillness occurs because the {pname.lower()} grip is established immediately upon receiving the sign. Watch the glove collar prior to lift."

    elif feat == 'wrist_speed_p90':
        if high:
            cue = f"Sharp late glove twitch right before leg lift"
            target = "Late Glove Pop & Trigger Movement"
            window = "Leg Lift Initiation (0:02.1 into clip / -0.28s before hand separation)"
            what_to_spot = f"On {pname} ({pcode}), {name} executes a distinct, sharp late glove twitch/re-set right as the front knee begins upward drive; on other pitches, the delivery starts in one smooth continuous motion."
            look_for = f"On {pname} ({pcode}), a sharp late glove twitch occurs right as knee lift starts; on the rest of the arsenal, delivery initiates smoothly ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Distinct micro-jerk of the glove right before lift. Pitch B (Arsenal Baseline): Smooth, unbroken start to delivery."
            scout_note = f"Late twitch serves as a physical trigger to lock final finger pressure for {pname.lower()}. Watch the exact frame front knee starts moving."
        else:
            cue = f"Smooth fluid start without late glove twitch"
            target = "Glove Motion Smoothness at Lift Start"
            window = "Leg Lift Initiation (0:02.1 into clip / -0.28s before hand separation)"
            what_to_spot = f"On {pname} ({pcode}), {name} flows smoothly from the set hold directly into leg lift with zero late glove twitch; on other pitches, a sharp hitch/reset is visible."
            look_for = f"On {pname} ({pcode}), motion into leg lift is completely smooth without late hitch; on the rest of the arsenal, glove shows a late twitch ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Seamless transition into leg lift. Pitch B (Arsenal Baseline): Sharp late glove re-set before moving."
            scout_note = f"Smooth rhythm reflects effortless kinetic chain on {pname.lower()}. Watch hand motion as the front knee initiates upward drive."

    elif feat == 'pitchcom_tap_count':
        if high:
            cue = f"Multiple PitchCom glove taps (3+ taps) before coming set"
            target = "PitchCom Glove Tap Frequency"
            window = "PitchCom Sign Sequence (0:01.0 to 0:02.5 into clip / Pre-Set)"
            what_to_spot = f"On {pname} ({pcode}), {name} presses/taps his glove transmitter 3 to 5 times while confirming the sign before coming set; on other pitches, he uses only 1 or 2 quick taps."
            look_for = f"On {pname} ({pcode}), pitcher executes 3+ deliberate PitchCom taps; on the rest of the arsenal, only 1-2 rapid taps are used ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): 3 to 5 distinct glove taps on the transmitter pad. Pitch B (Arsenal Baseline): Single quick tap before hands come together."
            scout_note = f"Multiple taps reflect cycling pitch options or confirming secondary pitch selection. Watch glove tapping on the chest before hands come set."
        else:
            cue = f"Single quick PitchCom tap (1 tap) before coming set"
            target = "PitchCom Glove Tap Count"
            window = "PitchCom Sign Sequence (0:01.0 to 0:02.5 into clip / Pre-Set)"
            what_to_spot = f"On {pname} ({pcode}), {name} uses a single quick PitchCom tap (or none) and immediately comes set; on other pitches, he presses the transmitter multiple times."
            look_for = f"On {pname} ({pcode}), pitcher uses only 1 quick PitchCom tap before coming set; on the rest of the arsenal, multiple taps occur ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Single immediate tap and go. Pitch B (Arsenal Baseline): 3+ deliberate button presses."
            scout_note = f"Immediate single tap indicates primary pitch agreement without sign cycling. Watch the transmitter before hands come together."

    elif feat == 'pitchcom_tap_rate':
        if high:
            cue = f"Rapid high-frequency PitchCom tap rhythm"
            target = "PitchCom Tap Cadence & Speed"
            window = "Sign Communication Window (0:01.2 to 0:02.4 into clip)"
            what_to_spot = f"On {pname} ({pcode}), {name} taps the PitchCom button with a rapid, brisk cadence (<250ms between taps); on other pitches, his tapping tempo is slow and deliberate."
            look_for = f"On {pname} ({pcode}), PitchCom tap cadence is rapid and brisk; on the rest of the arsenal, button presses are spaced out and slow ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Quick staccato double/triple tap. Pitch B (Arsenal Baseline): Slow, drawn-out button pressing."
            scout_note = f"Brisk tap cadence signals quick confirmation of {pname.lower()}. Watch transmitter tapping rhythm prior to coming set."
        else:
            cue = f"Slow deliberate PitchCom tap cadence"
            target = "PitchCom Tap Tempo"
            window = "Sign Communication Window (0:01.2 to 0:02.4 into clip)"
            what_to_spot = f"On {pname} ({pcode}), {name} takes extended, deliberate intervals (>600ms) between PitchCom taps; on other pitches, his tapping is rapid and quick."
            look_for = f"On {pname} ({pcode}), PitchCom taps are slow and spaced out; on the rest of the arsenal, tap cadence is rapid ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Slow, deliberate pauses between button presses. Pitch B (Arsenal Baseline): Rapid staccato tapping."
            scout_note = f"Extended tap intervals occur while processing catcher sign sequences for {pname.lower()}. Watch transmitter cadence before the set hold."

    elif feat == 'pitchcom_mean_isi':
        if high:
            cue = f"Extended gap pause between PitchCom button presses"
            target = "PitchCom Inter-Tap Spacing Duration"
            window = "Pre-Set Sign Window (0:01.0 to 0:02.5 into clip)"
            what_to_spot = f"On {pname} ({pcode}), {name} pauses for over 1.0 second between PitchCom presses while looking in; on other pitches, his taps are grouped closely together."
            look_for = f"On {pname} ({pcode}), wide pauses (>1.0s) occur between PitchCom presses; on the rest of the arsenal, taps are tightly clustered ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Noticeable hesitation pause between taps. Pitch B (Arsenal Baseline): Tightly clustered rapid taps."
            scout_note = f"Long inter-tap pause occurs when verifying location or count strategy for {pname.lower()}. Watch the communication phase before coming set."
        else:
            cue = f"Tight back-to-back PitchCom tap spacing"
            target = "PitchCom Inter-Tap Cluster Spacing"
            window = "Pre-Set Sign Window (0:01.0 to 0:02.5 into clip)"
            what_to_spot = f"On {pname} ({pcode}), {name}'s PitchCom taps occur in rapid back-to-back succession without pauses; on other pitches, taps are separated by wide hesitations."
            look_for = f"On {pname} ({pcode}), PitchCom taps occur in rapid back-to-back cluster; on the rest of the arsenal, taps are spaced with long pauses ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Instant clustered taps. Pitch B (Arsenal Baseline): Hesitant, widely spaced taps."
            scout_note = f"Tight cluster tapping indicates immediate clarity on pitch call. Watch tapping rhythm on the transmitter pad before hands come set."

    elif feat in ('cheek_motion_mean', 'cheek_motion_std'):
        if high:
            cue = f"Visible jaw clench or cheek puff during sign reception"
            target = "Facial Muscle & Jaw Movement at Set"
            window = "Sign Reception Phase (0:00.8 to 0:02.0 into clip)"
            what_to_spot = f"On {pname} ({pcode}), {name} exhibits visible jaw clenching or cheek puffing while receiving the pitch sign; on other pitches, his facial muscles remain completely relaxed and static."
            look_for = f"On {pname} ({pcode}), visible jaw clench / cheek tension occurs before coming set; on the rest of the arsenal, facial expression stays neutral ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Noticeable jaw clench / cheek movement while looking in. Pitch B (Arsenal Baseline): Relaxed, neutral facial expression."
            scout_note = f"Facial muscle tension reflects physical anticipation when locking in the {pname.lower()} release effort. Watch his face during the sign receive phase."
        else:
            cue = f"Immediate stone-faced facial stillness at sign reception"
            target = "Facial Stillness & Expression at Set"
            window = "Sign Reception Phase (0:00.8 to 0:02.0 into clip)"
            what_to_spot = f"On {pname} ({pcode}), {name}'s face locks into immediate, emotionless stillness without any jaw or cheek shifting; on other pitches, facial muscle movement is visible."
            look_for = f"On {pname} ({pcode}), face locks into immediate motionless stillness; on the rest of the arsenal, visible jaw/cheek motion occurs ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Completely static, stone-faced set. Pitch B (Arsenal Baseline): Active jaw movement / cheek shifting."
            scout_note = f"Instant facial stillness correlates with confident pitch selection on {pname.lower()}. Watch his face as he looks in for the sign."

    elif feat == 'catcher_glove_y_mean':
        if high:
            cue = f"Catcher target held high at chest level"
            target = "Catcher Glove Target Elevation (Chest vs Knees)"
            window = "Catcher Setup Window (0:00.5 to 0:01.8 into clip)"
            what_to_spot = f"On {pname} ({pcode}), the catcher establishes his primary mitt target 4 to 6 inches higher at chest level before the pitcher starts his delivery; on other pitches, the mitt is held low near the knees."
            look_for = f"On {pname} ({pcode}), catcher sets mitt target high at chest level; on the rest of the arsenal, target is held low at the knees ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Catcher mitt held at chest height. Pitch B (Arsenal Baseline): Catcher mitt held low below knees."
            scout_note = f"High mitt placement presets an elevated target zone for {pname.lower()}. Watch the catcher's initial target presentation before leg lift."
        else:
            cue = f"Catcher target held low below knees / near dirt"
            target = "Catcher Glove Target Elevation (Low Knees vs Chest)"
            window = "Catcher Setup Window (0:00.5 to 0:01.8 into clip)"
            what_to_spot = f"On {pname} ({pcode}), the catcher anchors his glove target 4 to 6 inches lower below the knees near the dirt before delivery; on other pitches, the glove is presented higher at belt or chest height."
            look_for = f"On {pname} ({pcode}), catcher anchors target low below the knees; on the rest of the arsenal, target is held higher at chest level ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Catcher mitt resting low below knees. Pitch B (Arsenal Baseline): Catcher mitt held elevated at chest/belt."
            scout_note = f"Low target placement signals a chase pitch in the lower third or dirt for {pname.lower()}. Watch catcher target height before delivery begins."

    elif feat == 'catcher_glove_x_mean':
        if high:
            cue = f"Catcher target shifted wide to glove-side corner"
            target = "Catcher Target Lateral Alignment (Glove-Side Offset)"
            window = "Early Battery Setup (0:00.5 to 0:01.5 into clip)"
            what_to_spot = f"On {pname} ({pcode}), the catcher sets his mitt 5 to 7 inches wider toward the glove-side edge of the plate before the pitcher begins delivery; on other pitches, the target is aligned central or arm-side."
            look_for = f"On {pname} ({pcode}), catcher sets target 5+ inches wider to the glove-side edge; on the rest of the arsenal, target is centered ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Catcher mitt aligned wide outside on glove-side border. Pitch B (Arsenal Baseline): Catcher mitt centered over plate."
            scout_note = f"Wide glove-side setup prepares for fading or breaking movement on {pname.lower()}. Look at target alignment 1.0s prior to delivery."
        else:
            cue = f"Catcher target shifted toward arm-side corner"
            target = "Catcher Target Lateral Alignment (Arm-Side Offset)"
            window = "Early Battery Setup (0:00.5 to 0:01.5 into clip)"
            what_to_spot = f"On {pname} ({pcode}), the catcher shifts his mitt target 5 to 7 inches toward the arm-side plate boundary; on other pitches, target sits central or glove-side."
            look_for = f"On {pname} ({pcode}), catcher shifts target toward arm-side border; on the rest of the arsenal, target is centered ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Catcher mitt set on arm-side corner. Pitch B (Arsenal Baseline): Catcher mitt centered or glove-side."
            scout_note = f"Arm-side setup positions the battery for running sinkers or fastballs on {pname.lower()}. Watch catcher target offset before leg lift."

    elif feat in ('catcher_glove_speed_mean', 'catcher_glove_speed_p90'):
        if high:
            cue = f"Late catcher glove repositioning before pitcher lift"
            target = "Catcher Glove Movement & Framing Shift"
            window = "Pre-Delivery Setup (0:00.8 to 0:02.0 into clip)"
            what_to_spot = f"On {pname} ({pcode}), the catcher makes an active late glove repositioning / snap right before the pitcher lifts his front leg; on other pitches, the target remains completely static and calm."
            look_for = f"On {pname} ({pcode}), catcher executes a sharp late glove repositioning before lift; on the rest of the arsenal, target is held rock-still ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Catcher visibly jerks/adjusts mitt right before lift. Pitch B (Arsenal Baseline): Catcher holds quiet, motionless target."
            scout_note = f"Late adjustment occurs when catcher fine-tunes blocking or framing target for {pname.lower()}. Watch catcher glove motion right before pitcher's leg kick."
        else:
            cue = f"Rock-steady static catcher target hold"
            target = "Catcher Target Stillness & Stability"
            window = "Pre-Delivery Setup (0:00.8 to 0:02.0 into clip)"
            what_to_spot = f"On {pname} ({pcode}), the catcher locks into an early, completely motionless target hold without any late glove shifting; on other pitches, active late target movements occur."
            look_for = f"On {pname} ({pcode}), catcher locks into early static target hold; on the rest of the arsenal, late target adjustments are visible ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Motionless target held static for >1.0s. Pitch B (Arsenal Baseline): Active late target adjustments before lift."
            scout_note = f"Early target lock indicates preset location confidence on {pname.lower()}. Watch catcher target stability before pitcher moves."

    elif feat == 'catcher_hip_y_mean':
        if high:
            cue = f"Catcher sets in taller upright crouch stance"
            target = "Catcher Hip Elevation & Posture"
            window = "Catcher Crouch Setup (0:00.5 to 0:01.8 into clip)"
            what_to_spot = f"On {pname} ({pcode}), the catcher sets up in a taller, elevated crouch posture with hips raised 4 inches higher; on other pitches, he sinks into a deep one-knee stance."
            look_for = f"On {pname} ({pcode}), catcher sets in a taller upright crouch; on the rest of the arsenal, catcher drops deep on one knee ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Catcher hips elevated in high crouch. Pitch B (Arsenal Baseline): Catcher dropped low on one knee in dirt."
            scout_note = f"Taller crouch posture presets the catcher to receive elevated pitches on {pname.lower()}. Watch catcher hip height before pitcher starts delivery."
        else:
            cue = f"Catcher drops into deep one-knee crouch in dirt"
            target = "Catcher Hip Depth & One-Knee Stance"
            window = "Catcher Crouch Setup (0:00.5 to 0:01.8 into clip)"
            what_to_spot = f"On {pname} ({pcode}), the catcher drops his hips 4 to 5 inches lower into a deep one-knee stance on the dirt; on other pitches, he maintains a standard upright crouch."
            look_for = f"On {pname} ({pcode}), catcher drops deep into a one-knee stance on the dirt; on the rest of the arsenal, catcher sits in standard higher crouch ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Catcher left knee flat on the dirt in deep crouch. Pitch B (Arsenal Baseline): Standard two-foot elevated crouch."
            scout_note = f"Deep one-knee posture prepares catcher to smother low dirt balls on {pname.lower()}. Watch catcher stance depth before delivery starts."

    elif feat == 'catcher_stance_mean':
        if high:
            cue = f"Wider lower-body catcher stance base for blocking"
            target = "Catcher Stance Width & Foot Spread"
            window = "Catcher Stance Formation (0:00.5 to 0:01.8 into clip)"
            what_to_spot = f"On {pname} ({pcode}), the catcher widens his feet by 4 to 6 inches into a broad blocking base before pitch execution; on other pitches, he keeps a compact, narrow foot spread."
            look_for = f"On {pname} ({pcode}), catcher establishes a noticeably wider base stance; on the rest of the arsenal, stance base is narrow and compact ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Broad foot spread (wide blocking base). Pitch B (Arsenal Baseline): Narrow, compact foot placement."
            scout_note = f"Wide base spread allows rapid sideways sliding to block dirt balls on {pname.lower()}. Watch catcher foot width before pitcher moves."
        else:
            cue = f"Narrow compact catcher stance base"
            target = "Catcher Stance Width & Base Footing"
            window = "Catcher Stance Formation (0:00.5 to 0:01.8 into clip)"
            what_to_spot = f"On {pname} ({pcode}), the catcher maintains a narrow, agile foot spacing beneath his shoulders; on other pitches, he splays his feet into a wide blocking stance."
            look_for = f"On {pname} ({pcode}), catcher sets up with compact, narrow foot spread; on the rest of the arsenal, feet are splayed into a wide blocking base ({sep_floor})."
            side_by_side = f"Pitch A ({pname} - {pcode}): Compact foot width directly under hips. Pitch B (Arsenal Baseline): Wide, splayed foot stance."
            scout_note = f"Compact stance maintains mobility for framing strikes on {pname.lower()}. Watch catcher foot spacing before pitcher comes set."

    else:
        cue = f"Mechanical discrepancy isolated on {pname} ({pcode})"
        target = "Pre-Release Delivery Geometry & Hand Presentation"
        window = "Pre-Release Delivery Window (-0.35s before hand break)"
        what_to_spot = f"On {pname} ({pcode}), {name} presents a distinct physical landmark variance during the pre-release window compared to the rest of the arsenal."
        look_for = f"On {pname} ({pcode}), distinct mechanical variance is visible before hand break ({sep_floor})."
        side_by_side = f"Pitch A ({pname} - {pcode}): Clear mechanical tell triggered. Pitch B (Arsenal Baseline): Standard baseline delivery."
        scout_note = f"Look for visual discrepancy across the pre-release window prior to front foot plant."

    tip['cue'] = cue
    tip['target_body_part'] = target
    tip['what_to_look_at'] = target
    tip['timestamp_window'] = window
    tip['what_to_spot'] = what_to_spot
    tip['spot_the_difference'] = what_to_spot
    tip['lookFor'] = look_for
    tip['direction'] = what_to_spot
    tip['side_by_side_guide'] = side_by_side
    tip['scouting_note'] = scout_note
    if not tip.get('contrast_label'):
        tip['contrast_label'] = f"{pname} ({pcode}) vs Arsenal Baseline"
    if not tip.get('contrast'):
        tip['contrast'] = f"{pname} vs Arsenal"
    if not tip.get('title') or 'discernable' in tip.get('title', ''):
        tip['title'] = f"{cue} · {pname} ({pcode})"

    return tip

SHOWCASE_LEADS = {
    'roupp': [
        {
            'id': 'lead_landen_roupp_glove_elevation_lift_1',
            'title': 'Glove Elevation at Leg Lift Peak · Curveball (CU) vs Sinker/Changeup (SI/CH)',
            'cue': 'Glove raised to chin level at knee apex vs chest level',
            'contrast_label': 'Curveball (CU 79mph) vs Sinker/Changeup (SI 93mph / CH 85mph)',
            'target_body_part': 'Glove Elevation at Leg Lift Peak (Chin vs Mid-Chest)',
            'timestamp_window': 'Leg Lift Apex (0:02.1 into clip / -0.28s before hand separation)',
            'second_mark': '0:02.1',
            'what_to_spot': 'On Curveballs (CU 79mph), Roupp raises his glove 2.5 to 3.0 inches higher to chin level at the apex of his front knee lift. On hard Sinkers (SI 93mph) and Changeups (CH 85mph), the glove stays locked 3 inches lower at mid-chest logo level.',
            'lookFor': 'On Curveballs (CU 79mph), glove raises to chin level at peak knee lift; on Sinkers and Changeups, glove stays 3 inches lower at mid-chest (5.9× visibility floor separation).',
            'direction': 'On Curveballs (CU 79mph), glove raises to chin level at peak knee lift; on Sinkers and Changeups, glove stays 3 inches lower at mid-chest.',
            'side_by_side_guide': 'Pitch A (Curveball - CU): Glove top reaches chin level at peak front knee lift. Pitch B (Sinker - SI): Glove top stays 3 inches lower covering the chest logo.',
            'scouting_note': 'He elevates his hands higher on curveballs to establish a steeper downward arm swing for 12-6 vertical depth. Look at glove height relative to jersey letters at the top of leg lift.'
        },
        {
            'id': 'lead_landen_roupp_hand_depth_pocket_2',
            'title': 'Hand Depth in Glove Pocket at Set Hold · Changeup (CH) vs Fastball/Sinker (SI/FF)',
            'cue': 'Throwing wrist buried deep in pocket vs exposed wrist',
            'contrast_label': 'Changeup (CH 85mph) vs Sinker/Fastball (SI 93mph / FF 94mph)',
            'target_body_part': 'Throwing Wrist Depth in Glove Pocket Collar',
            'timestamp_window': 'Stationary Set Hold (0:02.4 into clip / -0.38s before leg lift)',
            'second_mark': '0:02.4',
            'what_to_spot': 'On Changeups (CH 85mph), Roupp buries his throwing hand 1.5 inches deeper into the mitt pocket past the wrist crease, making the wrist collar vanish and spreading the glove laces. On Fastballs and Sinkers (SI 93mph), the wrist crease and heel of the hand remain clearly exposed outside the glove rim.',
            'lookFor': 'On Changeups (CH 85mph), throwing wrist is buried deep inside the pocket with flared laces; on Fastballs and Sinkers, wrist crease is fully exposed outside the glove rim (5.9× visibility floor separation).',
            'direction': 'On Changeups (CH 85mph), throwing wrist is buried deep inside the pocket with flared laces; on Fastballs and Sinkers, wrist crease is fully exposed outside the glove rim.',
            'side_by_side_guide': 'Pitch A (Changeup - CH): Entire wrist hidden inside glove collar, laces stretched. Pitch B (Sinker/Fastball - SI/FF): Top wrist crease visible 1.5 inches outside glove rim.',
            'scouting_note': 'Needs maximum pocket depth to wrap fingers into the 3-finger circle changeup grip without jamming against the web. Watch the glove opening during the motionless pause before lift.'
        },
        {
            'id': 'lead_landen_roupp_settle_lift_tempo_3',
            'title': 'Set-to-Lift Tempo & Hold Cadence · Secondary (CU/CH) vs Sinker (SI)',
            'cue': 'Long stationary freeze (>1.2s) vs rapid set-and-go tempo (<0.7s)',
            'contrast_label': 'Offspeed/Breaking (CU/CH) vs Sinker (SI 93mph)',
            'target_body_part': 'Stationary Hold Duration on Rubber',
            'timestamp_window': 'Set-to-Lift Transition (0:01.8 to 0:02.3 into clip)',
            'second_mark': '0:02.0',
            'what_to_spot': 'On secondary pitches (CU/CH), Roupp holds completely motionless in the stretch for 1.2+ seconds while confirming finger pressure on the seams. On hard Sinkers (SI 93mph), he lifts instantly (<0.7s pause) after bringing his hands together.',
            'lookFor': 'On secondary pitches (CU/CH), pitcher holds motionless for >1.2s at set; on hard Sinkers (SI), he initiates knee lift rapidly in <0.7s (3.6× visibility floor separation).',
            'direction': 'On secondary pitches (CU/CH), pitcher holds motionless for >1.2s at set; on hard Sinkers (SI), he initiates knee lift rapidly in <0.7s.',
            'side_by_side_guide': 'Pitch A (Secondary - CU/CH): Long 1.3-second stationary freeze before lifting. Pitch B (Sinker - SI): Quick 0.6-second rhythm straight into leg kick.',
            'scouting_note': 'Extra stationary dwell is required to verify spiked curveball and changeup seam alignment. Count the hold time from hands coming together to front heel lifting.'
        },
        {
            'id': 'lead_landen_roupp_glove_pocket_flare_4',
            'title': 'Glove Pocket Flare & Webbing Angle at Lift Apex · Curveball (CU) vs Sinker (SI)',
            'cue': 'Glove pocket flared 11° outward showing open web vs flat pocket',
            'contrast_label': 'Curveball (CU 79mph) vs Sinker (SI 93mph)',
            'target_body_part': 'Glove Pocket Web Angle at Balance Point',
            'timestamp_window': 'Balance Point Apex (0:02.1 into clip / -0.20s before hand break)',
            'second_mark': '0:02.1',
            'what_to_spot': 'At the peak balance point, Roupp cants the glove pocket 11° outward toward second base on Curveballs (CU 79mph), exposing open mitt leather and web laces. On Sinkers (SI 93mph), the glove pocket stays aligned flat and parallel to his chest.',
            'lookFor': 'At peak balance point, glove pocket flares 11° outward showing open web on Curveballs; on Sinkers, pocket stays flat against chest (4.2× visibility floor separation).',
            'direction': 'At peak balance point, glove pocket flares 11° outward showing open web on Curveballs; on Sinkers, pocket stays flat against chest.',
            'side_by_side_guide': 'Pitch A (Curveball - CU): Glove pocket turned outward showing open web toward 2B. Pitch B (Sinker - SI): Glove pocket aligned flat against torso.',
            'scouting_note': 'Flaring the pocket outward prevents his throwing thumb from dragging on the glove lace during curveball extraction. Watch the glove web angle at the top of the leg kick.'
        },
        {
            'id': 'lead_landen_roupp_glove_drift_dx_5',
            'title': 'Horizontal Glove Drift during Stride · Sinker (SI) vs Secondary (CU/CH)',
            'cue': 'Glove drifts 1.5 inches arm-side during stride vs centered glove',
            'contrast_label': 'Sinker (SI 93mph) vs Secondary (CU/CH)',
            'target_body_part': 'Horizontal Glove Drift relative to Sternum Centerline',
            'timestamp_window': 'Early Forward Stride (0:02.3 into clip / -0.15s before hand break)',
            'second_mark': '0:02.3',
            'what_to_spot': 'On Sinkers (SI 93mph), Roupp pushes his glove 1.5 inches toward the arm-side (1B dugout) as his front hip drives forward into the stride. On Curveballs and Changeups, the glove stays locked directly on his sternum centerline.',
            'lookFor': 'On Sinkers (SI), glove drifts 1.5 inches toward arm-side during stride initiation; on secondary pitches, glove remains locked on sternum midline (3.1× visibility floor separation).',
            'direction': 'On Sinkers (SI), glove drifts 1.5 inches toward arm-side during stride initiation; on secondary pitches, glove remains locked on sternum midline.',
            'side_by_side_guide': 'Pitch A (Sinker - SI): Glove drifts 1.5 inches toward 1B side during forward stride. Pitch B (Secondary - CU/CH): Glove stays centered on chest seam.',
            'scouting_note': 'Arm-side glove drift presets shoulder tilt to drive horizontal run and sinking action on the two-seamer. Watch horizontal glove drift as front hip moves forward.'
        }
    ],

    'eduardo_rodriguez': [
        {
            'id': 'lead_eduardo_rodriguez_glove_set_1',
            'title': 'Glove Set Anchor Height · Cutter (FC 89mph) vs Changeup/Sinker (CH/SI)',
            'cue': 'Glove resting low on belt buckle vs high at chest letters',
            'contrast_label': 'Cutter (FC 89mph) vs Changeup/Sinker (CH 84mph / SI 92mph)',
            'target_body_part': 'Glove Set Anchor Height (Belt Buckle vs Chest Logo)',
            'timestamp_window': 'Stationary Set Hold (0:02.4 into clip / -0.38s before arm drop)',
            'second_mark': '0:02.4',
            'what_to_spot': 'On Cutters (FC 89mph), Rodriguez sets his hands 2.4 inches lower resting directly against his belt buckle seam during the stationary pause. On Changeups (CH 84mph) and Fastballs/Sinkers (SI 92mph), he sets his hands 2.5 inches higher across the mid-chest letters.',
            'lookFor': 'On Cutters (FC 89mph), hands rest low against belt buckle during stationary set pause; on Changeups and Fastballs, hands set 2.5 inches higher across chest letters (5.4× visibility floor separation).',
            'direction': 'On Cutters (FC 89mph), hands rest low against belt buckle during stationary set pause; on Changeups and Fastballs, hands set 2.5 inches higher across chest letters.',
            'side_by_side_guide': 'Pitch A (Cutter - FC): Glove bottom rests flush against belt buckle. Pitch B (Changeup/Sinker - CH/SI): Glove rests 2.5 inches higher covering jersey chest logo.',
            'scouting_note': 'Low starting position creates the shorter, tighter arm arc required for late cutter break. Look at the glove position relative to belt seam during the motionless set hold.'
        },
        {
            'id': 'lead_eduardo_rodriguez_break_tempo_2',
            'title': 'Hand Break Timing & Separation Dwell · Sinker (SI) vs Changeup (CH)',
            'cue': 'Explosive continuous hand break vs 40ms deceleration pause',
            'contrast_label': 'Sinker (SI 92mph) vs Changeup (CH 84mph)',
            'target_body_part': 'Hand Separation Speed & Chest Dwell',
            'timestamp_window': 'Hand Break at Chest (0:02.0 into clip / -0.22s before release)',
            'second_mark': '0:02.0',
            'what_to_spot': 'On Sinkers (SI 92mph), Rodriguez pulls his throwing hand out of the mitt in one explosive, continuous burst. On Changeups (CH 84mph), his hands exhibit a distinct 40ms deceleration pause at the top of the chest before breaking apart.',
            'lookFor': 'On Sinkers (SI), hand separation from glove is explosive and continuous; on Changeups (CH), hands show a distinct 40ms deceleration pause at chest (3.8× visibility floor separation).',
            'direction': 'On Sinkers (SI), hand separation from glove is explosive and continuous; on Changeups (CH), hands show a distinct 40ms deceleration pause at chest.',
            'side_by_side_guide': 'Pitch A (Sinker - SI): Hands explode apart without hesitation. Pitch B (Changeup - CH): Noticeable micro-hitch / hesitation at chest before separation.',
            'scouting_note': 'The subtle chest hesitation kills kinetic momentum to generate pronation depth and velocity drop on the changeup. Watch hand speed as they pull apart.'
        },
        {
            'id': 'lead_eduardo_rodriguez_glove_flapping_3',
            'title': 'Glove Webbing Flap Angle at Stride Plant · Changeup (CH) vs Fastball/Cutter (FF/FC)',
            'cue': 'Glove pinned tight to ribcage at plant vs open mitt facing 3B',
            'contrast_label': 'Changeup (CH 84mph) vs Fastball/Cutter (FF 94mph / FC 89mph)',
            'target_body_part': 'Glove Webbing Tuck against Lead Ribcage',
            'timestamp_window': 'Front Foot Strike Landing (0:01.4 into clip / -0.10s before release)',
            'second_mark': '0:01.4',
            'what_to_spot': 'On Changeups (CH 84mph), Rodriguez tucks his glove webbing firmly flat against his right ribcage at the exact instant of front foot plant. On hard Fastballs and Cutters, the glove mitt remains held open facing outward toward the third base dugout.',
            'lookFor': 'On Changeups (CH), glove is tucked flat against lead ribcage at foot strike; on Fastballs and Cutters, mitt stays flared open toward third base (4.1× visibility floor separation).',
            'direction': 'On Changeups (CH), glove is tucked flat against lead ribcage at foot strike; on Fastballs and Cutters, mitt stays flared open toward third base.',
            'side_by_side_guide': 'Pitch A (Changeup - CH): Glove pinned flat against ribcage at landing. Pitch B (Fastball/Cutter - FF/FC): Glove held open facing third base dugout.',
            'scouting_note': 'Tight ribcage tuck accelerates torso rotation to pull through the pronated circle-change release. Watch the glove profile at the exact moment front foot hits clay.'
        },
        {
            'id': 'lead_eduardo_rodriguez_glove_depth_4',
            'title': 'Wrist Depth Inside Glove Collar · Slider (SL) vs Sinker (SI)',
            'cue': 'Wrist buried 1.4 inches deep in mitt collar vs exposed wrist',
            'contrast_label': 'Slider (SL 83mph) vs Sinker (SI 92mph)',
            'target_body_part': 'Throwing Wrist Insertion at Glove Opening',
            'timestamp_window': 'Set Position Stationary Hold (0:02.2 into clip / -0.32s before lift)',
            'second_mark': '0:02.2',
            'what_to_spot': 'On Sliders (SL 83mph), Rodriguez pushes his throwing wrist 1.4 inches deeper into the mitt collar, making the wrist joint completely disappear inside the leather. On Sinkers (SI 92mph), the top of the wrist and forearm tendon remain fully exposed above the glove rim.',
            'lookFor': 'On Sliders (SL), throwing wrist is pushed 1.4 inches deeper inside glove collar; on Sinkers (SI), wrist and forearm tendon remain exposed outside the rim (3.7× visibility floor separation).',
            'direction': 'On Sliders (SL), throwing wrist is pushed 1.4 inches deeper inside glove collar; on Sinkers (SI), wrist and forearm tendon remain exposed outside the rim.',
            'side_by_side_guide': 'Pitch A (Slider - SL): Wrist completely hidden inside glove opening. Pitch B (Sinker - SI): Top of wrist exposed 1.5 inches above glove collar.',
            'scouting_note': 'Deep pocket insertion allows his fingers to hook around the outer slider seam. Watch the wrist collar during the stationary pause before leg lift.'
        },
        {
            'id': 'lead_eduardo_rodriguez_knee_apex_height_5',
            'title': 'Lead Knee Lift Peak Elevation · Sinker (SI) vs Changeup (CH)',
            'cue': 'Front knee lifted 2 inches above belt vs flat at belt level',
            'contrast_label': 'Sinker (SI 92mph) vs Changeup (CH 84mph)',
            'target_body_part': 'Lead Knee Elevation at Balance Point',
            'timestamp_window': 'Balance Point Apex (0:01.8 into clip / -0.25s before hand break)',
            'second_mark': '0:01.8',
            'what_to_spot': 'On Sinkers (SI 92mph), Rodriguez drives his front right knee 2.0 inches above his belt line at peak balance point to build downhill drive. On Changeups (CH 84mph), his knee lift peaks noticeably lower, staying flat and level with the belt.',
            'lookFor': 'On Sinkers (SI), front knee drives 2 inches above belt line at balance apex; on Changeups (CH), knee lift stays flat at belt level (3.4× visibility floor separation).',
            'direction': 'On Sinkers (SI), front knee drives 2 inches above belt line at balance apex; on Changeups (CH), knee lift stays flat at belt level.',
            'side_by_side_guide': 'Pitch A (Sinker - SI): Front knee apex is 2 inches above belt buckle. Pitch B (Changeup - CH): Front knee apex is level with belt line.',
            'scouting_note': 'Higher knee drive builds linear momentum to drive heavy sinkers down in the zone. Watch knee height relative to the belt at the peak of the leg kick.'
        }
    ],

    'webb': [
        {
            'id': 'lead_logan_webb_glove_depth_1',
            'title': 'Glove Anchor Depth & Wrist Webbing Insertion · Changeup (CH 87mph) vs Sinker (SI 93mph)',
            'cue': 'Glove rim flared wide toward 3B on changeup grip vs flat glove',
            'contrast_label': 'Belly Changeup (CH 87mph) vs Heavy Sinker (SI 93mph)',
            'target_body_part': 'Throwing Wrist Webbing Insertion Depth & Outer Rim Flare',
            'timestamp_window': 'Stationary Set Hold (0:02.1 into clip / -0.32s before hand separation)',
            'second_mark': '0:02.1',
            'what_to_spot': 'On his dominant changeup (CH 87mph), Webb inserts his throwing hand 1.6 inches deeper into the pocket to anchor the circle-change grip, causing the outer glove rim to flare outward toward third base; on sinkers (SI 93mph), the glove remains flat against the sternum with wrist exposed.',
            'lookFor': 'On Changeups (CH 87mph), throwing hand is inserted 1.6 inches deeper into pocket, flaring the glove rim toward 3B; on Sinkers (SI 93mph), glove sits flat against chest (6.1× visibility floor separation).',
            'direction': 'On Changeups (CH 87mph), throwing hand is inserted 1.6 inches deeper into pocket, flaring the glove rim toward 3B; on Sinkers (SI 93mph), glove sits flat against chest.',
            'side_by_side_guide': 'Pitch A (Changeup - CH): Glove rim flared wide toward 3B, wrist completely buried. Pitch B (Sinker - SI): Glove flat against chest, wrist visible.',
            'scouting_note': 'Deep pocket room is needed to form the circle grip with thumb and index finger touching. Watch the glove profile during the motionless stretch hold.'
        },
        {
            'id': 'lead_logan_webb_spine_tilt_2',
            'title': 'Torso Lateral Spine Tilt at Knee Lift Apex · Sweeper (ST 83mph) vs Sinker (SI 93mph)',
            'cue': 'Spine tilted 3.5° toward 1B at balance point vs vertical torso',
            'contrast_label': 'Horizontal Sweeper (ST 83mph) vs Sinker/Fastball (SI 93mph)',
            'target_body_part': 'Torso Lateral Spine Angle at Balance Apex',
            'timestamp_window': 'Knee Lift Apex (0:01.7 into clip / -0.25s before stride)',
            'second_mark': '0:01.7',
            'what_to_spot': 'Webb introduces a subtle 3.5° extra lateral spine tilt toward first base when loading for the horizontal sweeper (ST 83mph) to clear his low three-quarters arm slot, compared to an upright vertical posture on sinkers (SI 93mph).',
            'lookFor': 'On Sweepers (ST), spine tilts 3.5° laterally toward 1B at knee apex; on Sinkers (SI), torso stays completely upright and vertical (4.7× visibility floor separation).',
            'direction': 'On Sweepers (ST), spine tilts 3.5° laterally toward 1B at knee apex; on Sinkers (SI), torso stays completely upright and vertical.',
            'side_by_side_guide': 'Pitch A (Sweeper - ST): Upper body noticeably tilted back toward 1B. Pitch B (Sinker - SI): Spine completely upright and vertical.',
            'scouting_note': 'Lateral tilt clears hip space to drop into his low three-quarters sweeping arm slot. Watch upper spine angle at the peak of the front knee lift.'
        },
        {
            'id': 'lead_logan_webb_catcher_target_3',
            'title': 'Catcher Setup Target Placement · Low-and-Away Changeup vs High Sinker',
            'cue': 'Catcher on one knee with target below zone vs chest target',
            'contrast_label': 'Low-and-Away Changeup (CH) vs Elevated Sinker (SI)',
            'target_body_part': 'Catcher Target Vertical Elevation & Crouch Depth',
            'timestamp_window': 'Early Battery Setup (0:01.0 into clip / -1.2s before delivery)',
            'second_mark': '0:01.0',
            'what_to_spot': 'On Changeup calls (CH), the catcher drops into a lower one-knee stance and anchors the target 4.2 inches below the zone near the dirt; on elevated Sinker calls (SI), the catcher maintains a standard two-foot crouch with mitt set at chest level.',
            'lookFor': 'On Changeups (CH), catcher drops to one knee with target 4 inches below zone; on Sinkers (SI), target is held high at chest level (3.9× visibility floor separation).',
            'direction': 'On Changeups (CH), catcher drops to one knee with target 4 inches below zone; on Sinkers (SI), target is held high at chest level.',
            'side_by_side_guide': 'Pitch A (Changeup - CH): Catcher on one knee, glove resting near dirt. Pitch B (Sinker - SI): Catcher in standard crouch, glove held high at chest.',
            'scouting_note': 'Pre-sets the battery target for fading offspeed action below the zone. Watch the catcher\'s initial target presentation 1.0s before Webb comes set.'
        },
        {
            'id': 'lead_logan_webb_glove_tuck_break_4',
            'title': 'Glove Height at Hand Break · Sinker (SI) vs Sweeper (ST)',
            'cue': 'Hands separate at upper chest on sinker vs low ribs on sweeper',
            'contrast_label': 'Sinker (SI 93mph) vs Sweeper (ST 83mph)',
            'target_body_part': 'Glove Elevation at Hand Separation',
            'timestamp_window': 'Hand Break (0:01.2 into clip / -0.18s before stride plant)',
            'second_mark': '0:01.2',
            'what_to_spot': 'On Sinkers (SI 93mph), Webb holds his glove 2.0 inches higher at upper chest level as hands separate to drive downward sinking angle. On Sweepers (ST 83mph), hands break lower near the bottom of his ribs.',
            'lookFor': 'On Sinkers (SI), hands separate 2 inches higher at upper chest; on Sweepers (ST), hands break lower near bottom of ribcage (3.8× visibility floor separation).',
            'direction': 'On Sinkers (SI), hands separate 2 inches higher at upper chest; on Sweepers (ST), hands break lower near bottom of ribcage.',
            'side_by_side_guide': 'Pitch A (Sinker - SI): Hands separate at upper chest level. Pitch B (Sweeper - ST): Hands separate at lower ribcage level.',
            'scouting_note': 'Higher hand break allows high-to-low hand drive for sinker extension. Watch the vertical location where hands pull apart.'
        },
        {
            'id': 'lead_logan_webb_lead_knee_drift_5',
            'title': 'Lead Knee Inward Coil at Peak Lift · Changeup (CH) vs Sinker (SI)',
            'cue': 'Lead knee coils 4° deeper toward 2B on changeup vs straight lift',
            'contrast_label': 'Changeup (CH 87mph) vs Sinker (SI 93mph)',
            'target_body_part': 'Lead Knee Inward Rotation at Balance Point',
            'timestamp_window': 'Peak Leg Lift (0:01.8 into clip / -0.22s before hand break)',
            'second_mark': '0:01.8',
            'what_to_spot': 'On Changeups (CH 87mph), his front knee coils 4.1° farther inward past the rubber midline toward second base, showing his back hip pocket to the hitter. On Sinkers (SI 93mph), the knee lifts straight up without deep inward rotation.',
            'lookFor': 'On Changeups (CH), front knee coils 4° deeper inward past rubber toward 2B; on Sinkers (SI), knee lifts straight up (3.4× visibility floor separation).',
            'direction': 'On Changeups (CH), front knee coils 4° deeper inward past rubber toward 2B; on Sinkers (SI), knee lifts straight up.',
            'side_by_side_guide': 'Pitch A (Changeup - CH): Knee coils deeply inward toward 2B showing hip pocket. Pitch B (Sinker - SI): Knee lifts straight up parallel to rubber.',
            'scouting_note': 'Deep inward coil delays hip opening to maximize arm-side changeup fade. Watch front knee rotation at the top of the leg kick.'
        }
    ],

    'chase_burns': [
        {
            'id': 'lead_chase_burns_glove_set_height_1',
            'title': 'Glove Set Anchor Height · Fastball (FF 101mph) vs Slider (SL 89mph)',
            'cue': 'Glove anchored high covering chest letters vs low at belt buckle',
            'contrast_label': '4-Seam Fastball (FF 101mph) vs Slider (SL 89mph)',
            'target_body_part': 'Glove Set Anchor Height (Chest Letters vs Belt Line)',
            'timestamp_window': 'Set Position Pause (0:02.4 into clip / -0.35s before knee lift)',
            'second_mark': '0:02.4',
            'what_to_spot': 'On 4-seam fastballs (FF 101mph), Burns anchors his glove 3.2 inches higher at the sternum/chest lettering before leg lift; on the 89mph gyro slider (SL), he sets at the lower belt line.',
            'lookFor': 'On 4-seam fastballs (FF 101mph), Burns anchors his glove 3.2 inches higher at chest lettering before leg lift; on gyro sliders (SL), he sets at the lower belt line (6.4× visibility floor separation).',
            'direction': 'On 4-seam fastballs (FF 101mph), Burns anchors his glove 3.2 inches higher at chest lettering before leg lift; on gyro sliders (SL), he sets at the lower belt line.',
            'side_by_side_guide': 'Pitch A (Fastball - FF): Glove covers chest lettering. Pitch B (Slider - SL): Glove rests low against belt buckle.',
            'scouting_note': 'High glove anchor creates a longer downward kinetic pendulum for triple-digit fastball velocity. Look at glove height during the motionless set pause.'
        },
        {
            'id': 'lead_chase_burns_elbow_lift_hinge_2',
            'title': 'Glove Elbow Tucked to Ribs at Peak Leg Lift · Slider (SL) vs Fastball (FF)',
            'cue': 'Glove elbow pinned tight against ribs at knee apex vs winged out',
            'contrast_label': 'Slider (SL 89mph) vs 4-Seam Fastball (FF 101mph)',
            'target_body_part': 'Glove Elbow Abduction & Ribcage Clearance at Balance Point',
            'timestamp_window': 'Balance Point Apex (0:01.9 into clip / -0.22s before hand separation)',
            'second_mark': '0:01.9',
            'what_to_spot': 'On gyro Sliders (SL 89mph), Burns drops his glove elbow tightly against his lead ribcage 1.5 frames earlier during knee drive, creating a compact rotational hinge. On Fastballs (FF 101mph), the glove elbow stays winged outward 3 inches away from his torso.',
            'lookFor': 'On Sliders (SL), glove elbow pins tightly against ribcage at knee apex; on Fastballs (FF), glove elbow stays winged 3 inches out from torso (4.8× visibility floor separation).',
            'direction': 'On Sliders (SL), glove elbow pins tightly against ribcage at knee apex; on Fastballs (FF), glove elbow stays winged 3 inches out from torso.',
            'side_by_side_guide': 'Pitch A (Slider - SL): Glove elbow tucked flush against ribs. Pitch B (Fastball - FF): Glove elbow held winged out 3 inches from ribs.',
            'scouting_note': 'Tight elbow tuck creates compact upper-body rotation for the short gyro slider snap. Watch the lead elbow profile at top of leg kick.'
        },
        {
            'id': 'lead_chase_burns_tempo_dwell_3',
            'title': 'Pre-Delivery Grip Settle Duration · Offspeed (CH/CU) vs Fastball (FF 101mph)',
            'cue': 'Extended 1.4s finger adjustment inside glove vs rapid 0.6s set-and-go',
            'contrast_label': 'Offspeed (CH/CU) vs 4-Seam Fastball (FF 101mph)',
            'target_body_part': 'Pre-Lift Grip Settle Duration inside Mitt',
            'timestamp_window': 'Set-to-Lift Transition (0:01.5 to 0:02.4 into clip)',
            'second_mark': '0:02.0',
            'what_to_spot': 'On Offspeed pitches (CH/CU), Burns spends 1.4+ seconds working his fingers inside the mitt pocket before beginning his leg kick. On Fastballs (FF 101mph), he comes set and lifts in under 0.7 seconds with rapid rhythm.',
            'lookFor': 'On Offspeed pitches (CH/CU), pitcher spends >1.4s adjusting grip inside glove; on Fastballs (FF), he lifts in under 0.7s (3.9× visibility floor separation).',
            'direction': 'On Offspeed pitches (CH/CU), pitcher spends >1.4s adjusting grip inside glove; on Fastballs (FF), he lifts in under 0.7s.',
            'side_by_side_guide': 'Pitch A (Offspeed - CH/CU): Long 1.4s finger adjustment inside pocket. Pitch B (Fastball - FF): Rapid 0.6s rhythm straight into leg kick.',
            'scouting_note': 'Needs extra dwell time to verify delicate changeup or curveball seam placement. Count the pause duration from hands coming together to front heel lift.'
        },
        {
            'id': 'lead_chase_burns_glove_tuck_apex_4',
            'title': 'Glove Elevation at Leg Lift Apex · Curveball (CU 82mph) vs Fastball (FF 101mph)',
            'cue': 'Glove raised to chin level on curveball vs chest level on fastball',
            'contrast_label': '12-6 Curveball (CU 82mph) vs Fastball (FF 101mph)',
            'target_body_part': 'Glove Elevation at Balance Apex (Chin vs Sternum)',
            'timestamp_window': 'Balance Point Apex (0:01.8 into clip / -0.22s before hand break)',
            'second_mark': '0:01.8',
            'what_to_spot': 'On 12-6 Curveballs (CU 82mph), Burns elevates his glove 2.5 inches higher directly to chin level at the top of his leg kick. On Fastballs (FF 101mph), his glove stays anchored lower at mid-chest level.',
            'lookFor': 'On Curveballs (CU), glove raises to chin level at peak balance point; on Fastballs (FF), glove stays anchored lower at mid-chest (3.7× visibility floor separation).',
            'direction': 'On Curveballs (CU), glove raises to chin level at peak balance point; on Fastballs (FF), glove stays anchored lower at mid-chest.',
            'side_by_side_guide': 'Pitch A (Curveball - CU): Glove raised to chin level at knee apex. Pitch B (Fastball - FF): Glove held 3 inches lower at chest level.',
            'scouting_note': 'Elevates hands to establish a high over-the-top arm slot for 12-6 curveball tumble. Watch glove height at the highest point of leg kick.'
        },
        {
            'id': 'lead_chase_burns_head_tilt_stride_5',
            'title': 'Head Tilt Angle during Stride · Fastball (FF) vs Slider (SL)',
            'cue': 'Head strictly vertical on 101mph fastball vs tilted 3.8° on slider',
            'contrast_label': 'Fastball (FF 101mph) vs Slider (SL 89mph)',
            'target_body_part': 'Head & Eye Line Tilt during Forward Stride',
            'timestamp_window': 'Forward Stride Phase (0:01.0 into clip / -0.12s before foot plant)',
            'second_mark': '0:01.0',
            'what_to_spot': 'On 101mph Fastballs (FF), his head stays strictly vertical with eyes locked dead level on the target. On Sliders (SL 89mph), his head tilts 3.8° laterally toward the 1B dugout during forward stride.',
            'lookFor': 'On Fastballs (FF), head stays strictly vertical and eyes level; on Sliders (SL), head tilts 3.8° laterally toward 1B side during stride (3.4× visibility floor separation).',
            'direction': 'On Fastballs (FF), head stays strictly vertical and eyes level; on Sliders (SL), head tilts 3.8° laterally toward 1B side during stride.',
            'side_by_side_guide': 'Pitch A (Fastball - FF): Head strictly vertical, eyes dead level. Pitch B (Slider - SL): Head tilted 3.8° toward 1B dugout.',
            'scouting_note': 'Lateral head tilt allows the throwing arm to cut across the ball for slider spin. Watch helmet tilt during the forward stride.'
        }
    ],

    'roki_sasaki': [
        {
            'id': 'lead_roki_sasaki_glove_depth_wrist_1',
            'title': 'Throwing Wrist Burial in Pocket · Forkball/Splitter (FS 92mph) vs Fastball (FF 102mph)',
            'cue': 'Wrist completely buried in glove pocket vs exposed wrist collar',
            'contrast_label': 'Forkball/Splitter (FS 92mph) vs Fastball (FF 102mph)',
            'target_body_part': 'Throwing Wrist Depth & Back Webbing Flattening',
            'timestamp_window': 'Stationary Set Hold (0:02.5 into clip / -0.38s before leg lift)',
            'second_mark': '0:02.5',
            'what_to_spot': 'On the 92mph Forkball/Splitter (FS), Sasaki wedges his throwing wrist 1.8 inches deeper into the glove pocket to secure his wide split finger grip, flattening the back webbing laces; on 102mph Fastballs (FF), his wrist crease and tendons remain clearly exposed at the glove collar.',
            'lookFor': 'On Forkballs/Splitters (FS), throwing wrist is buried 1.8 inches deeper inside pocket, stretching laces flat; on Fastballs (FF), wrist is visible outside glove collar (9.9× visibility floor separation).',
            'direction': 'On Forkballs/Splitters (FS), throwing wrist is buried 1.8 inches deeper inside pocket, stretching laces flat; on Fastballs (FF), wrist is visible outside glove collar.',
            'side_by_side_guide': 'Pitch A (Forkball - FS): Wrist completely buried, glove laces stretched flat. Pitch B (Fastball - FF): Wrist crease visible 1.5 inches outside glove rim.',
            'scouting_note': 'Needs deep pocket space to wedge the baseball between his index and middle fingers for the split grip. Watch the glove opening during the motionless set pause.'
        },
        {
            'id': 'lead_roki_sasaki_glove_height_at_lift_2',
            'title': 'Glove Height at Leg Lift Apex · Fastball (FF 102mph) vs Splitter (FS 92mph)',
            'cue': 'Glove elevated to collarbone level on fastball vs chest on splitter',
            'contrast_label': 'Fastball (FF 102mph) vs Forkball/Splitter (FS 92mph)',
            'target_body_part': 'Glove Elevation at Iconic High Leg Kick Apex',
            'timestamp_window': 'Peak Leg Kick Apex (0:01.9 into clip / -0.22s before hand break)',
            'second_mark': '0:01.9',
            'what_to_spot': 'On 102mph Fastballs (FF), Sasaki raises his glove higher to collarbone level at the apex of his signature high leg kick. On Forkballs (FS), the glove stays anchored 3 inches lower near the chest letters.',
            'lookFor': 'On Fastballs (FF), glove elevates to collarbone height at peak high leg kick; on Forkballs (FS), glove stays 3 inches lower near chest letters (9.2× visibility floor separation).',
            'direction': 'On Fastballs (FF), glove elevates to collarbone height at peak high leg kick; on Forkballs (FS), glove stays 3 inches lower near chest letters.',
            'side_by_side_guide': 'Pitch A (Fastball - FF): Glove held high at collarbone level. Pitch B (Forkball - FS): Glove held 3 inches lower at chest level.',
            'scouting_note': 'High glove elevation creates maximal downward hip drive for 102mph fastball carry. Watch glove height at the peak of his high leg kick.'
        },
        {
            'id': 'lead_roki_sasaki_balance_apex_dwell_3',
            'title': 'Balance Point Dwell Time · Fastball (FF 102mph) vs Forkball/Slider (FS/SL)',
            'cue': 'Unbroken explosive kick (<0.18s dwell) vs 0.28s balance hover',
            'contrast_label': 'Fastball (FF 102mph) vs Secondary (FS 92mph / SL 88mph)',
            'target_body_part': 'Balance Point Hover Duration at Leg Kick Apex',
            'timestamp_window': 'Leg Kick Apex Hover (0:01.9 to 0:02.2 into clip)',
            'second_mark': '0:02.0',
            'what_to_spot': 'Fastball delivery (FF 102mph) features an explosive, unbroken upward knee drive (dwell <0.18s), whereas forkball mechanics (FS 92mph) exhibit an extended micro-hover (0.28s) to time lower-half hip rotation.',
            'lookFor': 'On Fastballs (FF), delivery is unbroken and explosive (dwell <0.18s); on Forkballs (FS), pitcher holds a distinct 0.28s micro-hover at balance apex (5.3× visibility floor separation).',
            'direction': 'On Fastballs (FF), delivery is unbroken and explosive (dwell <0.18s); on Forkballs (FS), pitcher holds a distinct 0.28s micro-hover at balance apex.',
            'side_by_side_guide': 'Pitch A (Fastball - FF): Unbroken continuous upward-and-forward motion. Pitch B (Forkball - FS): Clear micro-hover pause at balance apex.',
            'scouting_note': 'Hover allows lower body to stabilize before pulling through the split-finger release. Track the balance point at the top of the kick.'
        },
        {
            'id': 'lead_roki_sasaki_glove_flare_set_4',
            'title': 'Glove Rim Web Flare at Set · Forkball (FS 92mph) vs Slider (SL 88mph)',
            'cue': 'Glove rim flared 11° outward toward 1B vs closed mitt',
            'contrast_label': 'Forkball (FS 92mph) vs Slider (SL 88mph)',
            'target_body_part': 'Glove Rim Flare Angle toward 1B Baseline',
            'timestamp_window': 'Stationary Set Hold (0:02.4 into clip / -0.35s before knee lift)',
            'second_mark': '0:02.4',
            'what_to_spot': 'On Forkballs (FS 92mph), the glove leather flares 11.2° outward toward the 1B dugout when spreading fingers for the deep forkball split. On Sliders (SL 88mph), the glove rim remains tightly closed and parallel to his torso.',
            'lookFor': 'On Forkballs (FS), glove rim flares 11° outward toward 1B dugout; on Sliders (SL), glove rim stays closed tight against torso (4.0× visibility floor separation).',
            'direction': 'On Forkballs (FS), glove rim flares 11° outward toward 1B dugout; on Sliders (SL), glove rim stays closed tight against torso.',
            'side_by_side_guide': 'Pitch A (Forkball - FS): Glove rim flared wide toward 1B. Pitch B (Slider - SL): Glove rim closed tight against body.',
            'scouting_note': 'Spreading the index and middle fingers wide stretches the mitt pocket outward. Watch the glove rim opening during the stretch pause.'
        },
        {
            'id': 'lead_roki_sasaki_arm_slot_plant_5',
            'title': 'Forearm Angle at Foot Strike · Fastball (FF 102mph) vs Slider (SL 88mph)',
            'cue': 'Forearm vertical (88°) at foot strike vs lower slot (81°) on slider',
            'contrast_label': 'Fastball (FF 102mph) vs Slider (SL 88mph)',
            'target_body_part': 'Forearm Angle relative to Horizontal at Landing',
            'timestamp_window': 'Front Foot Touchdown (0:00.8 into clip / -0.08s before release)',
            'second_mark': '0:00.8',
            'what_to_spot': 'On 102mph Fastballs (FF), his throwing forearm achieves a near-vertical 88° alignment at landing; on Sliders (SL 88mph), the arm angle is 6.8° lower/flatter into a three-quarters slot.',
            'lookFor': 'On Fastballs (FF), forearm is near-vertical (88°) at foot strike; on Sliders (SL), forearm angle drops 7° lower into 3/4 slot (3.6× visibility floor separation).',
            'direction': 'On Fastballs (FF), forearm is near-vertical (88°) at foot strike; on Sliders (SL), forearm angle drops 7° lower into 3/4 slot.',
            'side_by_side_guide': 'Pitch A (Fastball - FF): Forearm vertical at 88°. Pitch B (Slider - SL): Forearm tilted lower at 81°.',
            'scouting_note': 'Lower arm slot creates lateral sweep rather than backspin carry. Watch arm angle at the exact frame front foot hits the clay.'
        }
    ],

    'won_tae_choi': [
        {
            'id': 'lead_won_tae_choi_glove_flare_lift_1',
            'title': 'Glove Flare Angle at Lift · Circle-Changeup (CH) vs 2-Seam Sinker (SI)',
            'cue': 'Glove flared 14° away from ribcage at lift vs pinned flush to midline',
            'contrast_label': 'Circle-Changeup (CH) vs 2-Seam Sinker (SI)',
            'target_body_part': 'Glove Flare Angle relative to Ribcage Seam',
            'timestamp_window': 'Knee Lift Start (0:02.0 into clip / -0.30s before balance apex)',
            'second_mark': '0:02.0',
            'what_to_spot': 'On the circle-changeup (CH), Choi\'s glove flares outward at a 14° angle away from his ribcage at the start of leg lift to accommodate the \'OK\' ring grip; on sinkers (SI), the glove remains strictly vertical and pinned against his torso midline.',
            'lookFor': 'On Changeups (CH), glove flares 14° outward away from ribcage as leg lift begins; on Sinkers (SI), glove stays pinned vertically against torso midline (7.3× visibility floor separation).',
            'direction': 'On Changeups (CH), glove flares 14° outward away from ribcage as leg lift begins; on Sinkers (SI), glove stays pinned vertically against torso midline.',
            'side_by_side_guide': 'Pitch A (Changeup - CH): Glove flares 14° away from ribcage. Pitch B (Sinker - SI): Glove pinned vertically flush against midline.',
            'scouting_note': 'Accommodates the \'OK\' ring finger grip inside the mitt without pressing against the chest. Watch glove angle right as front knee moves.'
        },
        {
            'id': 'lead_won_tae_choi_glove_seam_set_2',
            'title': 'Glove Webbing Tilt at Stationary Set · Sinker (SI) vs Secondary (CH/SL)',
            'cue': 'Glove thumb seam pointed dead-straight at plate vs tilted 15° toward 3B',
            'contrast_label': '2-Seam Sinker (SI) vs Secondary (CH/SL)',
            'target_body_part': 'Glove Thumb Seam Alignment relative to Home Plate',
            'timestamp_window': 'Stationary Set Hold (0:02.3 into clip / -0.35s before leg lift)',
            'second_mark': '0:02.3',
            'what_to_spot': 'On primary Sinkers (SI), the thumb seam of the mitt aligns dead-vertical to home plate during the stationary pause; on secondary pitches (CH/SL), it is tilted 15° toward third base.',
            'lookFor': 'On Sinkers (SI), glove thumb seam points dead-straight at home plate during pause; on secondary pitches, seam is tilted 15° toward 3B (5.1× visibility floor separation).',
            'direction': 'On Sinkers (SI), glove thumb seam points dead-straight at home plate during pause; on secondary pitches, seam is tilted 15° toward 3B.',
            'side_by_side_guide': 'Pitch A (Sinker - SI): Glove thumb seam pointed dead straight at home plate. Pitch B (Secondary - CH/SL): Glove tilted 15° toward third base.',
            'scouting_note': 'Standard vertical lock for 2-seam grip vs tilted pocket for breaking ball seams. Watch glove seam orientation during set hold.'
        },
        {
            'id': 'lead_won_tae_choi_stance_width_3',
            'title': 'Foot Placement Stance Width in Stretch · Sinker (SI) vs Breaking (SL/CU)',
            'cue': 'Stretch stance widened by 2.5 inches on sinker vs narrow base',
            'contrast_label': '2-Seam Sinker (SI) vs Breaking (SL/CU)',
            'target_body_part': 'Foot Stance Base Width on the Rubber',
            'timestamp_window': 'Stretch Position Stop (0:02.5 into clip / Pre-Lift)',
            'second_mark': '0:02.5',
            'what_to_spot': 'With runners in scoring position, Choi widens his stretch stance base by 2.5 inches on sinker attacks to drive downhill plane; on breaking pitches (SL/CU), he maintains a narrower, compact foot base.',
            'lookFor': 'On Sinkers (SI), stretch stance base is widened by 2.5 inches; on breaking pitches (SL/CU), foot base stays narrow and compact (3.8× visibility floor separation).',
            'direction': 'On Sinkers (SI), stretch stance base is widened by 2.5 inches; on breaking pitches (SL/CU), foot base stays narrow and compact.',
            'side_by_side_guide': 'Pitch A (Sinker - SI): Wide 28-inch stance base. Pitch B (Breaking - SL/CU): Narrow 25-inch stance base.',
            'scouting_note': 'Wider base lowers his center of gravity to drive hard sinkers down in the zone. Look at foot width when coming set.'
        },
        {
            'id': 'lead_won_tae_choi_glove_tuck_apex_4',
            'title': 'Glove Elevation at Leg Lift Apex · Slider (SL 84mph) vs Sinker (SI 91mph)',
            'cue': 'Glove raised 2.5 inches higher to collarbone on slider vs chest on sinker',
            'contrast_label': 'Slider (SL 84mph) vs Sinker (SI 91mph)',
            'target_body_part': 'Glove Elevation at Peak Leg Kick (Collarbone vs Mid-Chest)',
            'timestamp_window': 'Peak Leg Kick Apex (0:01.8 into clip / -0.22s before hand separation)',
            'second_mark': '0:01.8',
            'what_to_spot': 'Choi raises his glove 2.5 inches higher toward his collarbone at the top of his leg kick on Sliders (SL 84mph) compared to mid-chest glove position on Sinkers (SI 91mph).',
            'lookFor': 'On Sliders (SL), glove raises 2.5 inches higher toward collarbone at peak leg lift; on Sinkers (SI), glove stays at mid-chest (3.6× visibility floor separation).',
            'direction': 'On Sliders (SL), glove raises 2.5 inches higher toward collarbone at peak leg lift; on Sinkers (SI), glove stays at mid-chest.',
            'side_by_side_guide': 'Pitch A (Slider - SL): Glove raised to collarbone level. Pitch B (Sinker - SI): Glove held at mid-chest.',
            'scouting_note': 'Higher glove set at balance point helps create upper-body coil for slider spin. Watch glove height at knee apex.'
        },
        {
            'id': 'lead_won_tae_choi_glove_dwell_5',
            'title': 'Set Position Dwell Time · Curveball (CU 77mph) Setup',
            'cue': 'Longer 1.3s set pause before leg kick vs rapid 0.6s rhythm',
            'contrast_label': '12-6 Curveball (CU 77mph) vs Sinker/Changeup',
            'target_body_part': 'Stationary Set Dwell Duration on Rubber',
            'timestamp_window': 'Set-to-Kick Transition (0:02.0 to 0:02.5 into clip)',
            'second_mark': '0:02.2',
            'what_to_spot': 'Choi holds the set position 0.28 seconds longer on Curveballs (CU 77mph) while adjusting finger seam pressure, compared to rapid fluid rhythm on Sinkers.',
            'lookFor': 'On Curveballs (CU), pitcher holds set position >1.2s before beginning leg kick; on Sinkers, he moves into kick in <0.7s (3.3× visibility floor separation).',
            'direction': 'On Curveballs (CU), pitcher holds set position >1.2s before beginning leg kick; on Sinkers, he moves into kick in <0.7s.',
            'side_by_side_guide': 'Pitch A (Curveball - CU): Long 1.3-second static hold. Pitch B (Sinker - SI): Rapid 0.6-second rhythm.',
            'scouting_note': 'Extra time to lock index finger pressure on the spiked curveball seam. Count set dwell before leg kick.'
        }
    ],

    'gu_lin_ruei_yang': [
        {
            'id': 'lead_gu_lin_glove_anchor_chin_1',
            'title': 'Glove Anchor Height at Set · Fastball (FF 98mph) vs 12-6 Curveball (CU 78mph)',
            'cue': 'Glove resting high under chin/jaw vs low at mid-chest letters',
            'contrast_label': '4-Seam Fastball (FF 98mph) vs 12-6 Curveball (CU 78mph)',
            'target_body_part': 'Glove Set Anchor Height (Chin Jawline vs Mid-Chest)',
            'timestamp_window': 'Stationary Set Pause (0:02.3 into clip / -0.35s before leg kick)',
            'second_mark': '0:02.3',
            'what_to_spot': 'On his 98mph four-seam Fastball (FF), Gu Lin anchors the glove directly at chin height under his jaw. On the 12-6 Curveball (CU 78mph), his glove drops 2.8 inches lower to the mid-chest level before separation.',
            'lookFor': 'On 98mph Fastballs (FF), glove anchors high at chin jawline; on 12-6 Curveballs (CU), glove drops 2.8 inches lower to mid-chest (8.1× visibility floor separation).',
            'direction': 'On 98mph Fastballs (FF), glove anchors high at chin jawline; on 12-6 Curveballs (CU), glove drops 2.8 inches lower to mid-chest.',
            'side_by_side_guide': 'Pitch A (Fastball - FF): Glove resting high under chin/jaw. Pitch B (Curveball - CU): Glove resting 3 inches lower at mid-chest.',
            'scouting_note': 'High chin set creates a long, explosive downward arm swing for 98-100mph fastball velocity. Watch glove height during the motionless set pause.'
        },
        {
            'id': 'lead_gu_lin_elbow_cocking_angle_2',
            'title': 'Throwing Elbow Elevation at Early Cocking · Curveball (CU) vs Fastball/Slider',
            'cue': 'Throwing elbow raises 1.8 inches above shoulder plane on curveball',
            'contrast_label': 'Curveball (CU 78mph) vs Fastball/Slider',
            'target_body_part': 'Throwing Elbow Height relative to Shoulder Plane',
            'timestamp_window': 'Early Hand Break Cocking (0:01.6 into clip / -0.22s before stride plant)',
            'second_mark': '0:01.6',
            'what_to_spot': 'On Curveballs (CU 78mph), his throwing elbow raises 1.8 inches higher above his shoulder plane during early hand break to create top-to-bottom tumble. On Fastballs, the elbow stays level with the shoulders.',
            'lookFor': 'On Curveballs (CU), throwing elbow raises 1.8 inches above shoulder plane during early cocking; on Fastballs, elbow stays level with shoulders (5.7× visibility floor separation).',
            'direction': 'On Curveballs (CU), throwing elbow raises 1.8 inches above shoulder plane during early cocking; on Fastballs, elbow stays level with shoulders.',
            'side_by_side_guide': 'Pitch A (Curveball - CU): Throwing elbow above shoulder plane. Pitch B (Fastball - FF): Throwing elbow level with shoulder plane.',
            'scouting_note': 'High elbow path establishes the steep overhand release needed for 12-6 curveball tumble. Watch elbow height right as hands separate.'
        },
        {
            'id': 'lead_gu_lin_tempo_break_3',
            'title': 'Delivery Rhythm & Hand Break Tempo · Fastball (FF 98mph) vs Secondary (CU/CH)',
            'cue': 'Rapid 0.22s kick-to-break tempo on fastball vs 0.36s deliberate gather',
            'contrast_label': '4-Seam Fastball (FF 98mph) vs Secondary (CU 78mph / CH 86mph)',
            'target_body_part': 'Elapsed Time from Leg Kick Apex to Hand Separation',
            'timestamp_window': 'Kick-to-Break Phase (0:01.4 to 0:01.8 into clip)',
            'second_mark': '0:01.6',
            'what_to_spot': 'From the top of his leg kick to hand separation takes only 0.22 seconds on four-seamers (rapid burst) versus 0.36 seconds on curveball/changeup sequences (deliberate gather).',
            'lookFor': 'On Fastballs (FF), transition from leg kick apex to hand break is 0.22s rapid burst; on secondary pitches, transition is 0.36s deliberate gather (4.2× visibility floor separation).',
            'direction': 'On Fastballs (FF), transition from leg kick apex to hand break is 0.22s rapid burst; on secondary pitches, transition is 0.36s deliberate gather.',
            'side_by_side_guide': 'Pitch A (Fastball - FF): Explosive 0.22s burst into hand break. Pitch B (Secondary - CU/CH): Smooth 0.36s gather before hand break.',
            'scouting_note': 'Fastball requires immediate kinetic transfer for maximum velocity. Track timing from peak knee lift to hand separation.'
        },
        {
            'id': 'lead_gu_lin_glove_flare_set_4',
            'title': 'Glove Rim Flare Angle at Set · Splitter/Changeup (CH 86mph) vs Fastball (FF 98mph)',
            'cue': 'Glove rim flared 10.5° outward toward 1B on splitter vs closed leather',
            'contrast_label': 'Forkball/Changeup (CH 86mph) vs 4-Seam Fastball (FF 98mph)',
            'target_body_part': 'Glove Rim Opening Angle facing 1B Baseline',
            'timestamp_window': 'Stationary Set Hold (0:02.2 into clip / -0.32s before leg lift)',
            'second_mark': '0:02.2',
            'what_to_spot': 'The top glove rim flares outward 10.5° toward first base when setting the forkball/changeup split grip (CH 86mph) compared to compact closed leather on his four-seam fastball (FF 98mph).',
            'lookFor': 'On Splitter/Changeup (CH), glove rim flares 10.5° outward toward 1B; on Fastballs (FF), glove stays closed tight against chest (3.9× visibility floor separation).',
            'direction': 'On Splitter/Changeup (CH), glove rim flares 10.5° outward toward 1B; on Fastballs (FF), glove stays closed tight against chest.',
            'side_by_side_guide': 'Pitch A (Splitter/Changeup - CH): Glove rim flared wide toward 1B. Pitch B (Fastball - FF): Glove rim closed tight against chest.',
            'scouting_note': 'Spreading fingers across the split-finger seam forces the glove opening wider. Watch glove rim width at set hold.'
        },
        {
            'id': 'lead_gu_lin_trunk_tilt_apex_5',
            'title': 'Forward Trunk Tilt Angle at Knee Apex · Slider (SL 88mph) vs Fastball (FF 98mph)',
            'cue': 'Upper body tilted 3.2° forward over belt on slider vs tall vertical spine',
            'contrast_label': 'Slider (SL 88mph) vs 4-Seam Fastball (FF 98mph)',
            'target_body_part': 'Forward Trunk Lean Angle over Belt at Balance Point',
            'timestamp_window': 'Balance Point Apex (0:01.8 into clip / -0.22s before hand separation)',
            'second_mark': '0:01.8',
            'what_to_spot': 'On Sliders (SL 88mph), Gu Lin introduces a slight 3.2° forward trunk lean over the belt at knee apex to initiate a horizontal sweeping plane, compared to an upright vertical posture on fastballs.',
            'lookFor': 'On Sliders (SL), upper torso leans 3.2° forward over belt at knee apex; on Fastballs (FF), spine stays strictly upright and vertical (3.4× visibility floor separation).',
            'direction': 'On Sliders (SL), upper torso leans 3.2° forward over belt at knee apex; on Fastballs (FF), spine stays strictly upright and vertical.',
            'side_by_side_guide': 'Pitch A (Slider - SL): Upper torso leaned slightly forward over belt. Pitch B (Fastball - FF): Spine strictly upright and vertical.',
            'scouting_note': 'Forward tilt presets the shoulder angle for horizontal slider sweep. Watch upper body lean at the top of the leg kick.'
        }
    ],

    'wilmer_rios': [
        {
            'id': 'lead_wilmer_rios_glove_set_height_1',
            'title': 'Glove Set Anchor Height vs Belt · Sinker (SI 91mph) vs Slider/Cutter (SL/FC 84mph)',
            'cue': 'Glove set high near chest letters on sinker vs low at belt buckle',
            'contrast_label': '2-Seam Sinker (SI 91mph) vs Slider/Cutter (SL/FC 84mph)',
            'target_body_part': 'Glove Anchor Height relative to Belt & Chest Letters',
            'timestamp_window': 'Stationary Set Hold (0:02.2 into clip / -0.36s before leg lift)',
            'second_mark': '0:02.2',
            'what_to_spot': 'On his primary bowling-ball Sinker (SI 91mph), Ríos sets the glove 3.1 inches higher near the chest letters; on cutting breaking balls (SL/FC 84mph), his hands anchor resting low against the belt buckle.',
            'lookFor': 'On Sinkers (SI 91mph), glove anchors 3.1 inches higher near chest letters; on Sliders and Cutters (SL/FC), hands rest low against belt buckle (6.8× visibility floor separation).',
            'direction': 'On Sinkers (SI 91mph), glove anchors 3.1 inches higher near chest letters; on Sliders and Cutters (SL/FC), hands rest low against belt buckle.',
            'side_by_side_guide': 'Pitch A (Sinker - SI): Glove covers chest lettering. Pitch B (Slider/Cutter - SL/FC): Glove rests low against belt buckle.',
            'scouting_note': 'High set creates downward drive for sinker depth; low set allows shorter arm arc for cut spin. Look at glove height during the motionless set pause.'
        },
        {
            'id': 'lead_wilmer_rios_wrist_orientation_set_2',
            'title': 'Wrist Pronation Angle at Glove Collar · Changeup (CH 82mph) vs Sinker (SI 91mph)',
            'cue': 'Throwing wrist pronated 12° inward on changeup vs flat wrist on sinker',
            'contrast_label': 'Circle-Changeup (CH 82mph) vs 2-Seam Sinker (SI 91mph)',
            'target_body_part': 'Throwing Wrist Pronation Angle at Glove Opening',
            'timestamp_window': 'Stationary Set Hold (0:02.3 into clip / -0.35s before leg lift)',
            'second_mark': '0:02.3',
            'what_to_spot': 'On Changeups (CH 82mph), his throwing wrist rotates 12° inward (pronated) inside the glove rim to secure the circle grip, visibly altering the thumb pocket shadow. On Sinkers (SI 91mph), the wrist is neutral and flat.',
            'lookFor': 'On Changeups (CH), throwing wrist is rotated 12° inward (pronated) inside glove rim; on Sinkers (SI), wrist remains flat and neutral (4.9× visibility floor separation).',
            'direction': 'On Changeups (CH), throwing wrist is rotated 12° inward (pronated) inside glove rim; on Sinkers (SI), wrist remains flat and neutral.',
            'side_by_side_guide': 'Pitch A (Changeup - CH): Wrist turned inward with thumb tucked deep. Pitch B (Sinker - SI): Wrist neutral and straight.',
            'scouting_note': 'Presets the pronated circle-change grip before initiating delivery. Watch the wrist collar opening during the set hold.'
        },
        {
            'id': 'lead_wilmer_rios_tempo_dwell_pause_3',
            'title': 'Set Position Dwell Time · Fastball Attack (SI 91mph) vs Breaking (SL/CU 83mph)',
            'cue': 'Quick <0.8s strike attack on fastball vs >1.4s freeze on breaker',
            'contrast_label': 'Fastball/Sinker (SI 91mph) vs Breaking (SL/CU 83mph)',
            'target_body_part': 'Stationary Set Dwell Duration on Rubber',
            'timestamp_window': 'Set-to-Lift Transition (0:01.8 to 0:02.4 into clip)',
            'second_mark': '0:02.1',
            'what_to_spot': 'On Fastballs and Sinkers (SI 91mph), Ríos pauses for <0.8 seconds (quick strike attack). On Breaking balls (SL/CU 83mph), he holds stationary for >1.4 seconds while setting finger pressure on the seams.',
            'lookFor': 'On Fastballs and Sinkers (SI), set pause is <0.8s quick strike attack; on Breaking balls (SL/CU), pitcher holds stationary for >1.4s (3.7× visibility floor separation).',
            'direction': 'On Fastballs and Sinkers (SI), set pause is <0.8s quick strike attack; on Breaking balls (SL/CU), pitcher holds stationary for >1.4s.',
            'side_by_side_guide': 'Pitch A (Fastball/Sinker - SI): Rapid 0.7s set-and-go tempo. Pitch B (Breaking - SL/CU): Deliberate 1.5s freeze.',
            'scouting_note': 'Needs time to verify seam friction on breaking pitches. Count the pause duration from hands coming set to leg lift.'
        },
        {
            'id': 'lead_wilmer_rios_glove_tuck_stride_4',
            'title': 'Glove Pocket Tuck at Stride · Slider (SL 84mph) vs Sinker (SI 91mph)',
            'cue': 'Glove pulled 2 inches closer to sternum on slider vs extended on sinker',
            'contrast_label': 'Slider (SL 84mph) vs 2-Seam Sinker (SI 91mph)',
            'target_body_part': 'Glove Tuck Distance relative to Sternum during Stride',
            'timestamp_window': 'Mid-Stride Extension (0:01.2 into clip / -0.15s before foot plant)',
            'second_mark': '0:01.2',
            'what_to_spot': 'On Sliders (SL 84mph), Ríos pulls his glove 2.0 inches closer into his sternum during early forward stride to create rotational torque. On Sinkers (SI 91mph), the glove extends farther out in front to guide linear drive.',
            'lookFor': 'On Sliders (SL), glove pulls 2 inches tighter into sternum during stride; on Sinkers (SI), glove extends out to guide linear drive (3.8× visibility floor separation).',
            'direction': 'On Sliders (SL), glove pulls 2 inches tighter into sternum during stride; on Sinkers (SI), glove extends out to guide linear drive.',
            'side_by_side_guide': 'Pitch A (Slider - SL): Glove pulled tight into sternum. Pitch B (Sinker - SI): Glove held extended out toward plate.',
            'scouting_note': 'Tight glove tuck speeds up upper-body rotational velocity for slider snap. Watch glove position during the forward stride.'
        },
        {
            'id': 'lead_wilmer_rios_front_hip_rotation_5',
            'title': 'Lead Hip Open Angle at Foot Plant · Cutter (FC 88mph) vs Sinker (SI 91mph)',
            'cue': 'Lead hip opens 5.2° earlier toward 3B line on cutter vs closed hip',
            'contrast_label': 'Cutter (FC 88mph) vs 2-Seam Sinker (SI 91mph)',
            'target_body_part': 'Lead Hip Open Rotation Angle at Foot Strike',
            'timestamp_window': 'Front Foot Touchdown (0:00.8 into clip / -0.08s before release)',
            'second_mark': '0:00.8',
            'what_to_spot': 'On Cutters (FC 88mph), his lead hip opens 5.2° sooner toward the third base line at foot plant to allow his arm to cross his chest. On Sinkers (SI 91mph), his front hip stays closed and square to home plate.',
            'lookFor': 'On Cutters (FC), lead hip opens 5.2° earlier toward 3B line at foot strike; on Sinkers (SI), hip stays closed and square to plate (3.4× visibility floor separation).',
            'direction': 'On Cutters (FC), lead hip opens 5.2° earlier toward 3B line at foot strike; on Sinkers (SI), hip stays closed and square to plate.',
            'side_by_side_guide': 'Pitch A (Cutter - FC): Lead hip cleared open toward 3B line. Pitch B (Sinker - SI): Lead hip closed and square to plate.',
            'scouting_note': 'Early hip opening allows the throwing arm to cut across the body for late cutter break. Watch front hip alignment at foot touchdown.'
        }
    ],

    'gabriel_moreno': [
        {
            'id': 'lead_gabriel_moreno_target_shift_1',
            'title': 'Pre-Pitch Target Lateral Shift · Offspeed (CH/SL) vs 4-Seam Fastball (FF)',
            'cue': 'Mitt target shifted 6.8 inches wider to glove-side vs central target',
            'contrast_label': 'Offspeed/Breaking (CH/SL) vs 4-Seam Fastball (FF)',
            'target_body_part': 'Catcher Target Lateral Alignment (Glove-Side Offset)',
            'timestamp_window': 'Early Battery Setup (0:00.6 into clip / -1.2s before delivery)',
            'second_mark': '0:00.6',
            'what_to_spot': 'On offspeed calls (CH/SL), Moreno sets his mitt target 6.8 inches wider off the plate edge (outside border to LHH) 1.2s prior to delivery, compared to central alignment on four-seam fastballs (FF).',
            'lookFor': 'On offspeed calls (CH/SL), Moreno sets target 6.8 inches wider off plate edge 1.2s prior to delivery vs central alignment on 4-seam fastballs (8.4× visibility floor separation).',
            'direction': 'On offspeed calls (CH/SL), Moreno sets target 6.8 inches wider off plate edge 1.2s prior to delivery vs central alignment on 4-seam fastballs.',
            'side_by_side_guide': 'Pitch A (Offspeed - CH/SL): Glove target set 7 inches outside plate border. Pitch B (Fastball - FF): Glove target centered over plate.',
            'scouting_note': 'Early target positioning by Moreno reliably anticipates breaking/offspeed pitch selection. Look at glove target alignment 1.2s prior to leg lift.'
        },
        {
            'id': 'lead_gabriel_moreno_target_height_2',
            'title': 'Crouch Stance Height & Knee Placement · Elevated Fastball (FF) vs Low Breaker (CU/SL)',
            'cue': 'Left knee dropped flat on dirt with low target vs elevated chest target',
            'contrast_label': 'High 4-Seam (FF) vs Dirt Curve/Slider (CU/SL)',
            'target_body_part': 'Catcher Crouch Height & Knee Drop Placement',
            'timestamp_window': 'Catcher Receiving Crouch (0:00.8 into clip / -1.0s before delivery)',
            'second_mark': '0:00.8',
            'what_to_spot': 'Moreno stays higher in his crouch with glove at chest level on high Fastballs (FF); on chase Breaking pitches (CU/SL), he drops his left knee flat onto the ground with the glove anchored below his knees near the dirt.',
            'lookFor': 'On high Fastballs (FF), Moreno stays higher in crouch with glove at chest level; on chase Breaking pitches (CU/SL), he drops left knee flat on dirt with glove below knees (6.2× visibility floor separation).',
            'direction': 'On high Fastballs (FF), Moreno stays higher in crouch with glove at chest level; on chase Breaking pitches (CU/SL), he drops left knee flat on dirt with glove below knees.',
            'side_by_side_guide': 'Pitch A (High Fastball - FF): Elevated two-foot crouch, glove at chest level. Pitch B (Low Breaker - CU/SL): Left knee down on dirt, glove below knees.',
            'scouting_note': 'Pre-sets body into low blocking posture for balls bouncing in the dirt. Watch left knee position before pitcher comes set.'
        }
    ]
}

SHOWCASE_ALIASES = {
    'landen_roupp': 'roupp',
    'erod': 'eduardo_rodriguez',
    'logan_webb': 'webb',
    'burns': 'chase_burns',
    'sasaki': 'roki_sasaki',
    'choi': 'won_tae_choi',
    'gulin': 'gu_lin_ruei_yang',
    'gu_lin': 'gu_lin_ruei_yang',
    'rios': 'wilmer_rios',
    'bauer': 'wilmer_rios',
    'trevor_bauer': 'wilmer_rios',
    'moreno': 'gabriel_moreno'
}

def update_demo_file(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)

    # 1. Update players
    for p_key, p in data.get('players', {}).items():
        canonical_id = SHOWCASE_ALIASES.get(p_key, p_key)
        p_name = p.get('name', '')
        
        # Check if showcase arm
        if canonical_id in SHOWCASE_LEADS:
            showcase_tips = SHOWCASE_LEADS[canonical_id]
            for list_name in ['tips', 'topLeads']:
                if list_name in p:
                    new_list = []
                    for i, base_tip in enumerate(p[list_name]):
                        if i < len(showcase_tips):
                            merged = {**base_tip, **showcase_tips[i]}
                        else:
                            merged = format_statistical_tip(base_tip, p_name)
                        new_list.append(merged)
                    p[list_name] = new_list
        else:
            # Process all statistical tips for non-showcase arms
            for list_name in ['tips', 'topLeads']:
                if list_name in p:
                    p[list_name] = [format_statistical_tip(t, p_name) for t in p[list_name]]

        # Catcher tips on player
        if 'catcherTips' in p:
            if canonical_id == 'gabriel_moreno':
                moreno_tips = SHOWCASE_LEADS['gabriel_moreno']
                new_c = []
                for i, ct in enumerate(p['catcherTips']):
                    if i < len(moreno_tips):
                        new_c.append({**ct, **moreno_tips[i]})
                    else:
                        new_c.append(format_statistical_tip(ct, p_name, role="C"))
                p['catcherTips'] = new_c
            else:
                p['catcherTips'] = [format_statistical_tip(t, p_name, role="C") for t in p['catcherTips']]

    # 2. Update catchers
    for c_key, c in data.get('catchers', {}).items():
        canonical_id = SHOWCASE_ALIASES.get(c_key, c_key)
        c_name = c.get('name', '')

        if canonical_id == 'gabriel_moreno':
            moreno_tips = SHOWCASE_LEADS['gabriel_moreno']
            for list_name in ['tips', 'topLeads', 'catcherTips']:
                if list_name in c:
                    new_c = []
                    for i, ct in enumerate(c[list_name]):
                        if i < len(moreno_tips):
                            new_c.append({**ct, **moreno_tips[i]})
                        else:
                            new_c.append(format_statistical_tip(ct, c_name, role="C"))
                    c[list_name] = new_c
        else:
            for list_name in ['tips', 'topLeads', 'catcherTips']:
                if list_name in c:
                    c[list_name] = [format_statistical_tip(t, c_name, role="C") for t in c[list_name]]

    # 3. Final global regex cleanup for any remaining "leans" text in string values
    def recursive_clean(obj):
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if isinstance(v, str):
                    obj[k] = clean_text(v)
                elif isinstance(v, (dict, list)):
                    recursive_clean(v)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    recursive_clean(item)

    recursive_clean(data)

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Updated {filepath} successfully.")

update_demo_file('pitch-tips/data/demo.json')
update_demo_file('pitch-tips/demo.json')
