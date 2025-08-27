"""
User Agreement and Legal Disclaimer Module

This module handles the display and acceptance of legal terms before platform usage.
Users must explicitly accept all terms before accessing any functionality.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import streamlit as st


class LegalAgreement:
    """Manages user acceptance of legal terms and disclaimers."""

    def __init__(self, use_database: bool = True):
        """Initialize the legal agreement handler.

        Args:
            use_database: Whether to use database (True) or JSON file (False)
        """
        self.use_database = use_database

        if use_database:
            from .legal_database import LegalDatabaseManager

            self.db = LegalDatabaseManager()
        else:
            # Fallback to JSON for testing/development
            self.acceptance_file = Path("data/legal_acceptances.json")
            self.acceptance_file.parent.mkdir(parents=True, exist_ok=True)

        # Key disclaimers that must be explicitly acknowledged
        self.critical_disclaimers = {
            "no_financial_advice": "I understand this platform does NOT provide financial advice",
            "no_legal_advice": "I understand this platform does NOT provide legal advice",
            "use_at_own_risk": "I accept that I use this platform entirely at my own risk",
            "no_liability": "I agree the platform has NO LIABILITY for any damages or losses",
            "seek_professionals": "I will consult qualified professionals before making decisions",
            "ai_limitations": "I understand AI-generated content may be incorrect or biased",
            "verify_information": "I will independently verify all information before acting",
            "no_guarantee": "I understand there is NO GUARANTEE of results or accuracy",
        }

    def get_session_hash(self) -> str:
        """Generate a unique session identifier.

        Returns:
            Hashed session ID
        """
        session_data = f"{st.session_state.get('session_id', '')}{datetime.now().date()}"
        return hashlib.sha256(session_data.encode()).hexdigest()[:16]

    def has_accepted_terms(self) -> bool:
        """Check if user has accepted terms in current session.

        Returns:
            True if terms accepted, False otherwise
        """
        return st.session_state.get("legal_terms_accepted", False)

    def record_acceptance(self, user_acknowledgments: Dict[str, bool]) -> bool:
        """Record user's acceptance of terms.

        Args:
            user_acknowledgments: Dictionary of acknowledged disclaimers

        Returns:
            True if all terms accepted, False otherwise
        """
        # Verify all critical disclaimers are acknowledged
        if not all(user_acknowledgments.values()):
            return False

        if self.use_database:
            # Use database for production
            user_id = st.session_state.get("user_id", self.get_session_hash())
            session_id = st.session_state.get("session_id", self.get_session_hash())
            ip_address = st.session_state.get("remote_ip", "127.0.0.1")

            additional_data = {
                "user_agent": st.session_state.get("user_agent", "unknown"),
                "platform_version": "1.0",
                "country_code": st.session_state.get("country_code", "US"),
            }

            success, acceptance_id = self.db.record_acceptance(
                user_identifier=user_id,
                session_id=session_id,
                ip_address=ip_address,
                disclaimers=list(user_acknowledgments.keys()),
                terms_version="1.0",
                additional_data=additional_data,
            )

            if success:
                st.session_state["legal_acceptance_id"] = acceptance_id
                st.session_state["legal_terms_accepted"] = True
                st.session_state["acceptance_timestamp"] = datetime.now()

            return success

        else:
            # Fallback to JSON file for development
            acceptance_record = {
                "session_hash": self.get_session_hash(),
                "timestamp": datetime.now().isoformat(),
                "disclaimers_accepted": list(user_acknowledgments.keys()),
                "ip_hash": hashlib.sha256(
                    st.session_state.get("remote_ip", "unknown").encode()
                ).hexdigest()[:16],
                "version": "1.0",
            }

            # Save to file (append mode)
            existing_records = []
            if self.acceptance_file.exists():
                try:
                    with open(self.acceptance_file, "r") as f:
                        existing_records = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError, PermissionError):
                    existing_records = []

            existing_records.append(acceptance_record)

            # Keep only last 1000 records for storage efficiency
            if len(existing_records) > 1000:
                existing_records = existing_records[-1000:]

            with open(self.acceptance_file, "w") as f:
                json.dump(existing_records, f, indent=2)

            # Mark as accepted in session
            st.session_state["legal_terms_accepted"] = True
            st.session_state["acceptance_timestamp"] = datetime.now()

            return True

    def display_agreement_modal(self) -> Optional[bool]:
        """Display the legal agreement modal.

        Returns:
            True if accepted, False if rejected, None if pending
        """
        # Initialize session state for stable layout
        if "legal_layout_initialized" not in st.session_state:
            st.session_state.legal_layout_initialized = True
            # Pre-initialize all checkbox states to prevent layout shifts
            for key in self.critical_disclaimers.keys():
                if f"legal_ack_{key}" not in st.session_state:
                    st.session_state[f"legal_ack_{key}"] = False
            if "final_legal_agreement" not in st.session_state:
                st.session_state["final_legal_agreement"] = False

        st.markdown(
            """
        <style>
        /* Fixed layout container */
        .legal-main-container {
            width: 100%;
            max-width: 900px;
            margin: 0 auto;
            position: relative;
        }

        .legal-container {
            background-color: #f8d7da;
            border: 2px solid #f5c6cb;
            border-radius: 10px;
            padding: 25px;
            margin: 20px 0;
            position: relative;
            width: 100%;
            box-sizing: border-box;
        }

        .legal-header {
            color: #721c24;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 25px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Fixed height sections */
        .warning-section {
            margin: 20px 0;
            min-height: 180px;
        }

        .advice-section {
            margin: 20px 0;
            min-height: 160px;
        }

        .limitations-section {
            margin: 20px 0;
            min-height: 140px;
        }

        .responsibilities-section {
            margin: 20px 0;
            min-height: 120px;
        }

        .acknowledgment-section {
            background-color: #e7f3ff;
            border: 2px solid #b3d9ff;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
            min-height: 400px;
            position: relative;
        }

        /* Prevent ALL checkbox layout shifts */
        .stCheckbox {
            margin: 10px 0 !important;
            height: 32px !important;
            min-height: 32px !important;
            max-height: 32px !important;
            display: block !important;
            position: relative !important;
        }

        .stCheckbox > label {
            height: 32px !important;
            min-height: 32px !important;
            max-height: 32px !important;
            display: flex !important;
            align-items: center !important;
            padding: 0 !important;
            margin: 0 !important;
            white-space: nowrap !important;
            overflow: visible !important;
        }

        .stCheckbox > label > div {
            height: 32px !important;
            min-height: 32px !important;
            max-height: 32px !important;
            display: flex !important;
            align-items: center !important;
        }

        /* Fixed button container */
        .acceptance-button-section {
            margin: 30px 0;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .progress-info {
            height: 40px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .button-row {
            width: 100%;
            max-width: 400px;
            height: 50px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        /* Prevent column resizing */
        .stColumns {
            display: flex !important;
            gap: 20px !important;
        }

        .stColumns > div {
            flex: 1 !important;
            min-width: 0 !important;
        }

        /* Footer section */
        .footer-section {
            margin-top: 30px;
            min-height: 60px;
        }

        /* Prevent text reflow */
        div[data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            padding: 5px 0 !important;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Create stable container structure
        main_container = st.container()

        with main_container:
            st.markdown('<div class="legal-main-container">', unsafe_allow_html=True)
            st.markdown('<div class="legal-container">', unsafe_allow_html=True)

            # Header - fixed height
            st.markdown(
                '<div class="legal-header">⚠️ LEGAL DISCLAIMER & TERMS OF USE ⚠️</div>',
                unsafe_allow_html=True,
            )

            # Warning section - fixed height
            warning_container = st.container()
            with warning_container:
                st.markdown('<div class="warning-section">', unsafe_allow_html=True)
                st.markdown(
                    """
                ### 🚨 **IMPORTANT: READ BEFORE PROCEEDING**

                This platform is for **INFORMATIONAL AND EDUCATIONAL PURPOSES ONLY**.

                **NO PROFESSIONAL ADVICE PROVIDED**
                """
                )
                st.markdown("</div>", unsafe_allow_html=True)

            # Advice columns - fixed height and structure
            advice_container = st.container()
            with advice_container:
                st.markdown('<div class="advice-section">', unsafe_allow_html=True)
                col1, col2 = st.columns(2, gap="medium")

                with col1:
                    st.error(
                        """
                    **NOT Financial Advice** ❌
                    - No investment recommendations
                    - No financial planning
                    - No tax guidance
                    - No trading advice
                    """
                    )

                with col2:
                    st.error(
                        """
                    **NOT Legal Advice** ❌
                    - No legal counsel
                    - No compliance guidance
                    - No regulatory advice
                    - No contract review
                    """
                    )
                st.markdown("</div>", unsafe_allow_html=True)

            # Limitations section - fixed height
            limitations_container = st.container()
            with limitations_container:
                st.markdown('<div class="limitations-section">', unsafe_allow_html=True)
                st.warning(
                    """
                ### ⚠️ **AI LIMITATIONS**
                - AI-generated content may be **INCORRECT**
                - Results may contain **BIASES** or **ERRORS**
                - Output can be **MISLEADING** or **INCOMPLETE**
                - Different queries may produce **INCONSISTENT** results
                """
                )
                st.markdown("</div>", unsafe_allow_html=True)

            # Responsibilities section - fixed height
            responsibilities_container = st.container()
            with responsibilities_container:
                st.markdown('<div class="responsibilities-section">', unsafe_allow_html=True)
                st.info(
                    """
                ### ✅ **YOUR RESPONSIBILITIES**
                1. **ALWAYS** consult qualified professionals before making decisions
                2. **INDEPENDENTLY VERIFY** all information provided
                3. **NEVER** rely solely on this platform for important decisions
                4. **UNDERSTAND** you use this platform at your own risk
                """
                )
                st.markdown("</div>", unsafe_allow_html=True)

            # Acknowledgments section - fixed height, stable checkboxes
            acknowledgments_container = st.container()
            with acknowledgments_container:
                st.markdown('<div class="acknowledgment-section">', unsafe_allow_html=True)
                st.markdown("### 📋 **Acknowledgments Required**")
                st.markdown("You must acknowledge each statement to proceed:")

                # Create all checkboxes with consistent structure
                acknowledgments = {}
                disclaimer_items = list(self.critical_disclaimers.items())

                for key, statement in disclaimer_items:
                    # Use session state directly to prevent rerendering
                    acknowledgments[key] = st.checkbox(
                        f"✓ {statement}",
                        key=f"legal_ack_{key}",
                        value=st.session_state.get(f"legal_ack_{key}", False),
                    )

                st.markdown("</div>", unsafe_allow_html=True)

            # Legal terms expander
            terms_container = st.container()
            with terms_container:
                st.markdown("### 📜 **Full Legal Terms**")
                with st.expander(
                    "Click to read full disclaimer and terms of service", expanded=False
                ):
                    legal_file = Path("LEGAL_DISCLAIMER.md")
                    if legal_file.exists():
                        st.markdown(legal_file.read_text())
                    else:
                        st.markdown("Full legal terms document not found. Contact administrator.")

            # Final agreement checkbox
            final_container = st.container()
            with final_container:
                final_agreement = st.checkbox(
                    "✓ **I have read, understood, and agree to ALL terms and conditions**",
                    key="final_legal_agreement",
                    value=st.session_state.get("final_legal_agreement", False),
                )

            # Final warning section - fixed height
            warning_final_container = st.container()
            with warning_final_container:
                st.markdown("### 🔴 **FINAL WARNING**")
                st.error(
                    """
                **BY PROCEEDING, YOU ACKNOWLEDGE:**
                - You assume **FULL RESPONSIBILITY** for your use of this platform
                - The platform has **NO LIABILITY** for any damages or losses
                - You will **NOT HOLD US RESPONSIBLE** for any negative outcomes
                - This is an **EXPERIMENTAL AI TOOL** not suitable for critical decisions
                """
                )

            # Button section - fixed height and layout
            button_container = st.container()
            with button_container:
                st.markdown('<div class="acceptance-button-section">', unsafe_allow_html=True)

                # Check acceptance status
                all_acknowledged = all(acknowledgments.values())
                all_terms_accepted = all_acknowledged and final_agreement

                # Progress indicator in fixed container
                total_items = len(acknowledgments) + 1
                accepted_items = sum(acknowledgments.values()) + (1 if final_agreement else 0)

                st.markdown('<div class="progress-info">', unsafe_allow_html=True)
                if not all_terms_accepted:
                    st.info(f"📋 Progress: {accepted_items}/{total_items} items accepted")
                else:
                    st.success("✅ All terms accepted - ready to proceed!")
                st.markdown("</div>", unsafe_allow_html=True)

                # Button in fixed layout
                st.markdown('<div class="button-row">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 2, 1])

                with col2:
                    if st.button(
                        (
                            "✅ I ACCEPT ALL TERMS"
                            if all_terms_accepted
                            else f"Accept All Terms ({accepted_items}/{total_items})"
                        ),
                        type="primary" if all_terms_accepted else "secondary",
                        disabled=not all_terms_accepted,
                        use_container_width=True,
                    ):
                        if all_terms_accepted:
                            if self.record_acceptance(acknowledgments):
                                st.success("✅ Terms accepted. Redirecting to platform...")
                                st.balloons()
                                return True
                            else:
                                st.error("❌ Error recording acceptance. Please try again.")
                                return None
                        else:
                            st.error("❌ You must acknowledge ALL statements to proceed")
                            return None

                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Footer section - fixed height
        footer_container = st.container()
        with footer_container:
            st.markdown('<div class="footer-section">', unsafe_allow_html=True)
            st.markdown("---")
            st.caption(
                """
            If you do not agree with these terms, please close this application immediately.
            For questions about these terms, consult with your legal advisor.
            """
            )
            st.markdown("</div>", unsafe_allow_html=True)

        return None

    @st.dialog("⚖️ Legal Agreement Required")
    def display_modal_agreement(self):
        """Display legal agreement in a modal dialog."""

        st.markdown(
            """
        <style>
        .modal-content {
            max-height: 70vh;
            overflow-y: auto;
            padding: 10px;
        }
        .legal-header {
            color: #721c24;
            text-align: center;
            margin-bottom: 20px;
        }
        .critical-warning {
            color: #dc3545;
            font-weight: bold;
            text-align: center;
            margin: 15px 0;
        }
        .checkbox-container {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
        }
        .progress-container {
            text-align: center;
            margin: 15px 0;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="modal-content">', unsafe_allow_html=True)

        # Header
        st.markdown('<div class="legal-header">', unsafe_allow_html=True)
        st.markdown("## ⚠️ LEGAL DISCLAIMER & TERMS OF USE")
        st.markdown("</div>", unsafe_allow_html=True)

        # Important notice
        st.error(
            """
        **🚨 IMPORTANT: This platform is for INFORMATIONAL AND EDUCATIONAL PURPOSES ONLY.**

        **NO PROFESSIONAL ADVICE PROVIDED**
        """
        )

        # Two column layout for advice types
        col1, col2 = st.columns(2)

        with col1:
            st.warning(
                """
            **NOT Financial Advice** ❌
            - No investment recommendations
            - No financial planning
            - No tax guidance
            - No trading advice
            """
            )

        with col2:
            st.warning(
                """
            **NOT Legal Advice** ❌
            - No legal counsel
            - No compliance guidance
            - No regulatory advice
            - No contract review
            """
            )

        # AI Limitations
        st.info(
            """
        ### ⚠️ **AI LIMITATIONS & YOUR RESPONSIBILITIES**

        **AI Issues:**
        - AI-generated content may be **INCORRECT**
        - Results may contain **BIASES** or **ERRORS**
        - Output can be **MISLEADING** or **INCOMPLETE**

        **Your Responsibilities:**
        1. **ALWAYS** consult qualified professionals before making decisions
        2. **INDEPENDENTLY VERIFY** all information provided
        3. **NEVER** rely solely on this platform for important decisions
        4. **UNDERSTAND** you use this platform at your own risk
        """
        )

        # Acknowledgments section
        st.markdown('<div class="checkbox-container">', unsafe_allow_html=True)
        st.markdown("### 📋 **Required Acknowledgments**")
        st.markdown("**You must accept ALL statements to proceed:**")
        st.info(
            "💡 **Tip**: Click '📜 Full Terms' below to view the complete legal disclaimer on GitHub."
        )

        # Collect acknowledgments
        acknowledgments = {}
        for key, statement in self.critical_disclaimers.items():
            acknowledgments[key] = st.checkbox(f"✓ {statement}", key=f"modal_legal_ack_{key}")

        # Final agreement checkbox
        final_agreement = st.checkbox(
            "✓ **I have read, understood, and agree to ALL terms and conditions**",
            key="modal_final_legal_agreement",
        )

        st.markdown("</div>", unsafe_allow_html=True)

        # Progress indicator
        all_acknowledged = all(acknowledgments.values())
        all_terms_accepted = all_acknowledged and final_agreement
        total_items = len(acknowledgments) + 1
        accepted_items = sum(acknowledgments.values()) + (1 if final_agreement else 0)

        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        if not all_terms_accepted:
            st.info(f"📋 Progress: {accepted_items}/{total_items} items accepted")
        else:
            st.success("✅ All terms accepted - ready to proceed!")
        st.markdown("</div>", unsafe_allow_html=True)

        # Final warning
        st.error(
            """
        ### 🔴 **FINAL WARNING**
        **BY PROCEEDING, YOU ACKNOWLEDGE:**
        - You assume **FULL RESPONSIBILITY** for your use of this platform
        - The platform has **NO LIABILITY** for any damages or losses
        - You will **NOT HOLD US RESPONSIBLE** for any negative outcomes
        - This is an **EXPERIMENTAL AI TOOL** not suitable for critical decisions
        """
        )

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("❌ Decline", type="secondary", use_container_width=True):
                st.error("❌ You must accept the terms to use this platform.")
                st.stop()

        with col2:
            # Link to full legal terms on GitHub
            github_legal_url = "https://github.com/UMainLove/business_intelligence_platform/blob/main/LEGAL_DISCLAIMER.md"
            st.markdown(
                f'<a href="{github_legal_url}" target="_blank" style="text-decoration: none;">'
                f'<button style="width: 100%; padding: 10px; background-color: #f0f2f6; border: 1px solid #d1d5db; border-radius: 4px; cursor: pointer;">'
                f"📜 Full Terms</button></a>",
                unsafe_allow_html=True,
            )

        with col3:
            if st.button(
                (
                    "✅ Accept All Terms"
                    if all_terms_accepted
                    else f"Accept ({accepted_items}/{total_items})"
                ),
                type="primary" if all_terms_accepted else "secondary",
                disabled=not all_terms_accepted,
                use_container_width=True,
            ):
                if all_terms_accepted:
                    if self.record_acceptance(acknowledgments):
                        st.success("✅ Terms accepted! Welcome to the platform.")
                        st.balloons()
                        # Clear the modal state to prevent re-display
                        for key in acknowledgments.keys():
                            if f"modal_legal_ack_{key}" in st.session_state:
                                del st.session_state[f"modal_legal_ack_{key}"]
                        if "modal_final_legal_agreement" in st.session_state:
                            del st.session_state["modal_final_legal_agreement"]
                        st.rerun()
                    else:
                        st.error("❌ Error recording acceptance. Please try again.")
                else:
                    st.error("❌ You must acknowledge ALL statements to proceed")

        st.markdown("</div>", unsafe_allow_html=True)

    def enforce_agreement(self) -> bool:
        """Enforce legal agreement before allowing platform access.

        Returns:
            True if user has accepted terms, False otherwise
        """
        if not self.has_accepted_terms():
            # Show modal dialog for legal agreement
            self.display_modal_agreement()
            return False  # Block access until accepted

        return True

    def display_disclaimer_footer(self):
        """Display a persistent disclaimer footer."""
        st.markdown("---")
        st.caption(
            """
        ⚠️ **Disclaimer**: This platform provides information for educational purposes only.
        Not financial or legal advice. Use at your own risk. Always consult professionals.
        [View Full Terms](/#legal-disclaimer)
        """
        )


def require_legal_acceptance(func):
    """Decorator to require legal acceptance before function execution.

    Args:
        func: Function to wrap with legal requirement

    Returns:
        Wrapped function that enforces legal acceptance
    """

    def wrapper(*args, **kwargs):
        legal = LegalAgreement()
        if legal.enforce_agreement():
            return func(*args, **kwargs)
        return None

    return wrapper
