// lib/data/campus_locations.dart
//
// Shared campus location registry used by both CampusMapScreen
// and LocationPickerScreen.

import 'package:latlong2/latlong.dart';

/// Known landmark positions per college.
/// Structure: { collegeId: { locationLabel: LatLng } }
const Map<String, Map<String, LatLng>> campusLocations = {};

/// Fallback centre coordinate per college (used when no specific
/// landmark is matched).
const Map<String, LatLng> collegeCentres = {};

/// Resolves a [LatLng] from a college ID and optional location label.
/// Falls back to the college centre, then to the geographic centre of India.
LatLng resolveLocation(String collegeId, String? locationLabel) {
  if (locationLabel != null) {
    final byCollege = campusLocations[collegeId];
    if (byCollege != null) {
      final exact = byCollege[locationLabel];
      if (exact != null) return exact;
    }
  }
  return collegeCentres[collegeId] ?? const LatLng(20.5937, 78.9629);
}
