
    if DEMO_MODE:
        st.info(
            "Battery readings are unavailable in demo mode because Streamlit Cloud "
            "cannot read your laptop's battery. The application impact table below "
            "uses sample application data only."
        )
        if data["applications"]:
            impact = estimate_process_impact(data["applications"])
            if impact:
                st.dataframe(pd.DataFrame(impact[:10]), use_container_width=True, hide_index=True)
        st.caption("Relative CPU/memory impact is not a measurement of actual battery drain.")
    else:
        try:
            battery = get_battery_insights()

            if not battery["available"]:
                st.info(battery["message"])
            else:
                b1, b2, b3 = st.columns(3)

                b1.metric(
                    "Battery level",
                    f'{battery["percent"]:.0f}%',
                )

                b2.metric(
                    "Power status",
                    "Plugged in" if battery["plugged_in"] else "On battery",
                )

                b3.metric(
                    "Estimated remaining time",
                    battery["remaining_time"],
                )

            st.subheader("Battery health")

            health = get_windows_battery_health()

            if health["available"]:
                st.metric(
                    "Estimated battery health",
                    f'{health["health_percent"]:.1f}%',
                )

                st.caption(
                    f'Original capacity: {health["design_capacity_mwh"]:,} mWh · '
                    f'Current full-charge capacity: '
                    f'{health["full_charge_capacity_mwh"]:,} mWh'
                )
            else:
                st.info(health["message"])

            st.subheader("Applications with the highest resource impact")

            if data["applications"]:
                impact = estimate_process_impact(data["applications"])

                if impact:
                    st.dataframe(
                        pd.DataFrame(impact[:10]),
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.caption(
                        "This ranking estimates relative CPU and memory impact. "
                        "It does not measure each application's actual battery drain."
                    )
                else:
                    st.info("Application usage data is not available.")
            else:
                st.info("No application telemetry is available.")

        except Exception as error:
            st.error(f"Battery analysis could not run: {error}")


# =========================================================
# DEVELOPER MODE
# =========================================================

if developer_mode:
    with st.expander("Raw telemetry payload"):
        st.json(data["raw"])


# =========================================================
# HOW IT WORKS
# =========================================================

with st.expander("How SoftSense works"):
    st.markdown(
        """
        **Live monitoring:** In live mode, the agent collects system and application
        metrics and sends them to the Flask backend. In demo mode, all displayed
        telemetry values are illustrative sample data, not readings from your PC.

        **Predictive warnings:** SoftSense stores historical measurements
        and estimates disk-space trends. Forecasts need sufficient history.

        **AI assistant:** The assistant uses current telemetry to explain
        potential performance problems. It needs a configured API key.

        **Cleanup advisor:** In live/local mode, scans selected folders for large
        files, older downloads, and duplicates. It is disabled in cloud demo mode
        because cloud hosting cannot access files on your laptop.

        **Battery insights:** In live/local mode, displays available battery data.
        It does not read your laptop's battery in cloud demo mode.

        SoftSense provides recommendations. It does not automatically
        terminate processes or delete files.
        """
    )


# =========================================================
# AUTO REFRESH
# =========================================================

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()