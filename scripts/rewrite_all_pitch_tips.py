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
        # Fallback for any other custom feature
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

print('Module loaded.')
