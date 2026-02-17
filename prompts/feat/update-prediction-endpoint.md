The prediction endpoint should interface with the user via a horizontal card component that contains the following information:

 - Risk Level: 3 different levels of risk: {low, medium, high}, the way this risk level is generated is via the following logic
    If the number of hours TAPS was last sighted was:
    - 0-1 hours: High Risk
    - 1-2 hours: Low Risk
    - 2-4 hours: Medium Risk
    - >4 hours: High Risk
    - Not spotted today: Medium Risk (also default / fallback risk)

 - Risk Bar: 3 bars of increasing height from left to right, will be for the UI

 - Risk Detail / Message: A message that will display with the above information that provides the user with more details. Some examples include: 
    - "TAPS was last spotted <x> hours ago at <parking structure>"
    - "TAPS has not been sighted today"

For implementation, you should examine the current prediction endpoint, and observe all parts of the app that it is interfacing with. This means that you should examine the @warnabrotha/ directory, where the iOS implementation is, and the @android/ directory, where the android implementation. Make sure that you are making appropriate updates and changes that accurately reflect the changes that you make to the prediction endpoint.
