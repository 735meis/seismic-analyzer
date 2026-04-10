"""
Educational Trivia System - Daily earthquake and seismology knowledge challenges.
"""

import streamlit as st
import random
from datetime import datetime
from typing import Dict, List


# Trivia question bank
TRIVIA_QUESTIONS = [
    {
        'id': 1,
        'question': 'What magnitude is considered a "major" earthquake?',
        'options': ['M 5.0-5.9', 'M 6.0-6.9', 'M 7.0-7.9', 'M 8.0-8.9'],
        'correct': 2,
        'explanation': 'Major earthquakes are classified as M 7.0-7.9 and can cause serious damage over larger areas. They occur about 15 times per year globally.'
    },
    {
        'id': 2,
        'question': 'Where do most earthquakes occur?',
        'options': ['Ocean floors', 'Plate boundaries', 'Mountain peaks', 'Volcanic calderas'],
        'correct': 1,
        'explanation': 'About 90% of earthquakes occur along plate boundaries where tectonic plates interact through collision, subduction, or sliding past each other.'
    },
    {
        'id': 3,
        'question': 'What is the Richter scale?',
        'options': [
            'A measure of earthquake intensity',
            'A logarithmic magnitude scale',
            'A damage assessment tool',
            'A seismograph type'
        ],
        'correct': 1,
        'explanation': 'The Richter scale is a logarithmic scale, meaning each whole number increase represents a 10x increase in amplitude and ~31.6x more energy release.'
    },
    {
        'id': 4,
        'question': 'What is the minimum magnitude humans can typically feel?',
        'options': ['M 1.0', 'M 2.0', 'M 3.0', 'M 4.0'],
        'correct': 2,
        'explanation': 'Earthquakes around M 3.0 are typically the threshold for human perception, though this varies based on depth, distance, and local geology.'
    },
    {
        'id': 5,
        'question': 'What is the deepest recorded earthquake depth?',
        'options': ['70 km', '300 km', '500 km', '700 km'],
        'correct': 3,
        'explanation': 'The deepest earthquakes occur at depths up to 700 km in subduction zones, where cold, dense oceanic plates sink into the mantle.'
    },
    {
        'id': 6,
        'question': 'What is an earthquake "swarm"?',
        'options': [
            'A series of aftershocks',
            'Multiple earthquakes with no clear main shock',
            'Simultaneous quakes in different locations',
            'Earthquakes caused by volcanic activity'
        ],
        'correct': 1,
        'explanation': 'An earthquake swarm is a sequence of many earthquakes with no single dominant main shock, often associated with volcanic or geothermal activity.'
    },
    {
        'id': 7,
        'question': 'What was the strongest earthquake ever recorded?',
        'options': ['M 8.8 Chile 2010', 'M 9.0 Japan 2011', 'M 9.5 Chile 1960', 'M 9.2 Alaska 1964'],
        'correct': 2,
        'explanation': 'The 1960 Valdivia earthquake in Chile measured M 9.5, the strongest ever recorded. It killed ~1,600 people and generated a tsunami that reached Hawaii and Japan.'
    },
    {
        'id': 8,
        'question': 'What is the "Ring of Fire"?',
        'options': [
            'A volcanic crater chain',
            'A Pacific Ocean seismic belt',
            'An earthquake prediction system',
            'A geothermal energy zone'
        ],
        'correct': 1,
        'explanation': 'The Ring of Fire is a horseshoe-shaped belt around the Pacific Ocean where ~90% of earthquakes occur due to active plate boundaries and volcanic activity.'
    },
    {
        'id': 9,
        'question': 'What is a foreshock?',
        'options': [
            'The first wave to arrive',
            'A smaller quake before a larger one',
            'An earthquake warning system',
            'A deep underground tremor'
        ],
        'correct': 1,
        'explanation': 'A foreshock is a smaller earthquake that precedes a larger one. However, it\'s impossible to know if a quake is a foreshock until the main shock occurs.'
    },
    {
        'id': 10,
        'question': 'What does USGS stand for?',
        'options': [
            'United States Geologic Service',
            'Universal Seismic Grid System',
            'United States Geological Survey',
            'Underground Seismology Group'
        ],
        'correct': 2,
        'explanation': 'USGS stands for United States Geological Survey, the scientific agency that monitors earthquakes, volcanoes, and other geological phenomena.'
    },
    {
        'id': 11,
        'question': 'Can animals predict earthquakes?',
        'options': [
            'Yes, scientifically proven',
            'No, it\'s a myth',
            'Yes, but only certain species',
            'No reliable scientific evidence'
        ],
        'correct': 3,
        'explanation': 'Despite many anecdotal reports, there is no reliable scientific evidence that animals can predict earthquakes. Unusual animal behavior may coincide with other environmental changes.'
    },
    {
        'id': 12,
        'question': 'What is liquefaction?',
        'options': [
            'When lava melts rock',
            'When soil behaves like liquid during shaking',
            'When water causes erosion',
            'When ice melts rapidly'
        ],
        'correct': 1,
        'explanation': 'Liquefaction occurs when water-saturated soil loses strength during earthquake shaking, causing buildings to sink and structures to collapse.'
    },
    {
        'id': 13,
        'question': 'What percentage of earthquakes occur underwater?',
        'options': ['30%', '50%', '70%', '90%'],
        'correct': 3,
        'explanation': 'About 90% of earthquakes occur underwater along mid-ocean ridges and subduction zones. Most are too small to generate tsunamis.'
    },
    {
        'id': 14,
        'question': 'What is the "Big One" referring to?',
        'options': [
            'Any M8.0+ earthquake',
            'The largest earthquake ever',
            'A predicted major California quake',
            'The next major global disaster'
        ],
        'correct': 2,
        'explanation': 'The "Big One" refers to a predicted major earthquake (M7.8+) expected along the San Andreas Fault in California, which could affect millions of people.'
    },
    {
        'id': 15,
        'question': 'How long does an earthquake typically last?',
        'options': ['1-2 seconds', '10-30 seconds', '1-2 minutes', '5-10 minutes'],
        'correct': 1,
        'explanation': 'Most earthquakes last 10-30 seconds, though major quakes can last 1-3 minutes. The 2011 Japan M9.0 quake lasted about 6 minutes!'
    },
    {
        'id': 16,
        'question': 'What are P-waves and S-waves?',
        'options': [
            'Types of ocean waves',
            'Seismic wave types',
            'Sound wave frequencies',
            'Electromagnetic waves'
        ],
        'correct': 1,
        'explanation': 'P-waves (primary) and S-waves (secondary) are types of seismic body waves. P-waves are faster compressional waves, while S-waves are slower shear waves.'
    },
    {
        'id': 17,
        'question': 'Which U.S. state has the most earthquakes?',
        'options': ['California', 'Alaska', 'Hawaii', 'Oklahoma'],
        'correct': 1,
        'explanation': 'Alaska has the most earthquakes, averaging 40,000 per year! Most are small and occur along the Aleutian subduction zone.'
    },
    {
        'id': 18,
        'question': 'What is an aftershock?',
        'options': [
            'A delayed shock response',
            'A smaller quake after the main shock',
            'A secondary earthquake wave',
            'A building collapse effect'
        ],
        'correct': 1,
        'explanation': 'Aftershocks are smaller earthquakes that occur after a main shock as the crust adjusts. They can continue for days, months, or even years.'
    },
    {
        'id': 19,
        'question': 'What is the difference between magnitude and intensity?',
        'options': [
            'Magnitude measures energy, intensity measures effects',
            'They are the same thing',
            'Magnitude is older, intensity is modern',
            'Intensity is measured by instruments'
        ],
        'correct': 0,
        'explanation': 'Magnitude measures the energy released at the source (objective), while intensity measures the effects at specific locations (subjective, varies by distance).'
    },
    {
        'id': 20,
        'question': 'What is the Modified Mercalli Intensity Scale?',
        'options': [
            'A magnitude measurement scale',
            'A damage and shaking intensity scale',
            'A seismograph calibration tool',
            'A tsunami warning system'
        ],
        'correct': 1,
        'explanation': 'The Modified Mercalli Intensity (MMI) scale measures the effects and damage of an earthquake from I (not felt) to XII (total destruction), based on observations.'
    }
]


def get_daily_question() -> Dict:
    """
    Get the daily trivia question based on today's date.

    Returns:
        Dictionary with question, options, correct answer, and explanation
    """
    # Use day of year as seed for consistent daily question
    day_of_year = datetime.now().timetuple().tm_yday
    random.seed(day_of_year)

    question = random.choice(TRIVIA_QUESTIONS)

    # Reset seed to avoid affecting other randomness
    random.seed()

    return question


def render_trivia_sidebar():
    """
    Render the daily trivia challenge in the sidebar.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧠 Daily Trivia Challenge")

    # Get today's question
    question = get_daily_question()

    # Initialize session state for trivia
    if 'trivia_answered_today' not in st.session_state:
        st.session_state.trivia_answered_today = False
        st.session_state.trivia_correct = False
        st.session_state.trivia_selected = None

    # Show question
    st.sidebar.markdown(
        f'<div class="glass-card" style="padding: 0.75rem; margin: 0.5rem 0; font-size: 0.9375rem;">'
        f'{question["question"]}'
        f'</div>',
        unsafe_allow_html=True
    )

    # Answer options
    if not st.session_state.trivia_answered_today:
        selected = st.sidebar.radio(
            "Your answer:",
            question['options'],
            key='trivia_answer',
            label_visibility='collapsed'
        )

        if st.sidebar.button("Submit Answer", key='trivia_submit'):
            st.session_state.trivia_selected = selected
            st.session_state.trivia_answered_today = True

            # Check if correct
            selected_index = question['options'].index(selected)
            is_correct = (selected_index == question['correct'])
            st.session_state.trivia_correct = is_correct

            # Award points (imported from gamification module)
            try:
                from src.gamification import award_points, increment_stat

                if is_correct:
                    award_points('trivia_correct')
                    increment_stat('trivia_correct')
                    st.sidebar.success("✅ Correct! +20 points")
                else:
                    award_points('trivia_attempt')
                    increment_stat('trivia_attempts')
                    st.sidebar.error("❌ Not quite! +5 points for trying")

            except ImportError:
                # If gamification not yet integrated, just show feedback
                if is_correct:
                    st.sidebar.success("✅ Correct!")
                else:
                    st.sidebar.error("❌ Not quite!")

            # Force rerun to show explanation
            st.rerun()

    # Show result and explanation if answered
    if st.session_state.trivia_answered_today:
        if st.session_state.trivia_correct:
            st.sidebar.success("✅ Correct!")
        else:
            st.sidebar.error(f"❌ Correct answer: {question['options'][question['correct']]}")

        # Show explanation
        st.sidebar.info(question['explanation'])

        # Reset button for testing (in production, this would reset at midnight)
        if st.sidebar.button("Try Another Question", key='trivia_reset'):
            st.session_state.trivia_answered_today = False
            st.session_state.trivia_correct = False
            st.session_state.trivia_selected = None
            st.rerun()


def get_trivia_stats() -> Dict:
    """
    Get user's trivia statistics from session state.

    Returns:
        Dictionary with correct answers, total attempts, accuracy
    """
    stats = st.session_state.get('user_stats', {})

    correct = stats.get('trivia_correct', 0)
    attempts = stats.get('trivia_attempts', 0)
    total = correct + attempts

    accuracy = (correct / total * 100) if total > 0 else 0

    return {
        'correct': correct,
        'attempts': attempts,
        'total': total,
        'accuracy': accuracy
    }
