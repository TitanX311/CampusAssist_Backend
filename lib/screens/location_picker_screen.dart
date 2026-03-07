// lib/screens/location_picker_screen.dart
//
// A full-screen map picker. User can:
//   1. Tap a known campus landmark from the quick-select list
//   2. Search for a landmark by name
//   3. Long-press anywhere on the map to drop a custom pin
//   4. Drag the pin to fine-tune
//
// Returns a PickedLocation object to the caller via Navigator.pop().
//
// Dependencies (add to pubspec.yaml):
//   flutter_map: ^6.1.0
//   latlong2: ^0.9.0

import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../theme/app_theme.dart';
import '../data/campus_locations.dart';

// ── Return type ───────────────────────────────────────────────────────────────
class PickedLocation {
  final String label;
  final LatLng latLng;
  const PickedLocation({required this.label, required this.latLng});
}

// ─────────────────────────────────────────────────────────────────────────────

class LocationPickerScreen extends StatefulWidget {
  final String collegeId;
  final String collegeName;

  /// Pre-selected location to show when opening (optional)
  final PickedLocation? initial;

  /// Label typed in the text field before opening map (optional)
  final String initialLabel;

  const LocationPickerScreen({
    super.key,
    required this.collegeId,
    required this.collegeName,
    this.initial,
    this.initialLabel = '',
  });

  @override
  State<LocationPickerScreen> createState() => _LocationPickerScreenState();
}

class _LocationPickerScreenState extends State<LocationPickerScreen>
    with TickerProviderStateMixin {
  late final MapController _mapCtrl;
  late final AnimationController _pinBounce;
  late final AnimationController _sheetCtrl;
  late final Animation<double> _pinAnim;
  late final Animation<Offset> _sheetSlide;

  LatLng? _pickedLatLng;
  String _pickedLabel = '';
  bool _geocoding = false;

  final _searchCtrl = TextEditingController();
  String _searchQuery = '';

  // Known campus landmarks for this college
  late final Map<String, LatLng> _landmarks;
  late final LatLng _collegeCentre;

  @override
  void initState() {
    super.initState();
    _mapCtrl = MapController();

    _landmarks = campusLocations[widget.collegeId] ?? {};
    _collegeCentre =
        collegeCentres[widget.collegeId] ?? const LatLng(20.5937, 78.9629);

    if (widget.initial != null) {
      _pickedLatLng = widget.initial!.latLng;
      _pickedLabel = widget.initial!.label;
    }

    // Pre-fill search with whatever the user typed in the text field
    if (widget.initialLabel.isNotEmpty && _pickedLabel.isEmpty) {
      _searchQuery = widget.initialLabel;
      _searchCtrl.text = widget.initialLabel;
    }

    // Pin drop bounce
    _pinBounce = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );
    _pinAnim = CurvedAnimation(parent: _pinBounce, curve: Curves.elasticOut);

    // Bottom sheet slide
    _sheetCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 380),
    );
    _sheetSlide = Tween<Offset>(
      begin: const Offset(0, 1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _sheetCtrl, curve: Curves.easeOutCubic));

    if (_pickedLatLng != null) {
      _pinBounce.forward();
      _sheetCtrl.forward();
    }

    // When opened with a typed label, geocode it and fly the map there.
    if (widget.initial == null && widget.initialLabel.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _geocodeAndFly(widget.initialLabel);
      });
    }
  }

  /// Geocodes [query] using Nominatim (OpenStreetMap) — no API key needed.
  /// Priority:
  ///   1. Exact/partial match in known campus landmarks → fly & pin instantly
  ///   2. Nominatim result → fly to it, drop pin with typed label
  ///   3. Fallback → fly to college centre, drop pin with typed label
  Future<void> _geocodeAndFly(String query) async {
    if (!mounted) return;
    final q = query.toLowerCase().trim();

    // ── 1. Try campus landmarks first (instant, no network) ──────────────
    for (final entry in _landmarks.entries) {
      if (entry.key.toLowerCase() == q ||
          entry.key.toLowerCase().startsWith(q) ||
          entry.key.toLowerCase().contains(q)) {
        _pickLandmark(entry.key, entry.value);
        return;
      }
    }

    // ── 2. Nominatim geocode via Dio ──────────────────────────────────────
    setState(() => _geocoding = true);
    try {
      final centre = _collegeCentre;
      final dio = Dio(
        BaseOptions(
          headers: {'User-Agent': 'CampusAssist/1.0'},
          connectTimeout: const Duration(seconds: 6),
          receiveTimeout: const Duration(seconds: 6),
        ),
      );

      final response = await dio.get<List<dynamic>>(
        'https://nominatim.openstreetmap.org/search',
        queryParameters: {
          'q': '$query, ${widget.collegeName}, India',
          'format': 'json',
          'limit': '1',
          'viewbox':
              '${centre.longitude - 0.1},${centre.latitude + 0.1},'
              '${centre.longitude + 0.1},${centre.latitude - 0.1}',
          'bounded': '0',
        },
      );

      final results = response.data ?? [];
      if (results.isNotEmpty && mounted) {
        final lat = double.parse(results[0]['lat'] as String);
        final lon = double.parse(results[0]['lon'] as String);
        final pos = LatLng(lat, lon);
        setState(() => _geocoding = false);
        _mapCtrl.move(pos, 17.0);
        _pickLandmark(query, pos);
        return;
      }
    } on DioException {
      // Network error — fall through to fallback
    }

    // ── 3. Fallback: fly to college centre, pin with typed label ──────────
    if (mounted) {
      setState(() => _geocoding = false);
      _mapCtrl.move(_collegeCentre, 16.5);
      _pickLandmark(query, _collegeCentre);
    }
  }

  @override
  void dispose() {
    _pinBounce.dispose();
    _sheetCtrl.dispose();
    _mapCtrl.dispose();
    _searchCtrl.dispose();
    super.dispose();
  }

  void _pickLandmark(String label, LatLng pos) {
    setState(() {
      _pickedLatLng = pos;
      _pickedLabel = label;
      _searchCtrl.clear();
      _searchQuery = '';
    });
    _mapCtrl.move(pos, 17.5);
    _pinBounce
      ..reset()
      ..forward();
    _sheetCtrl.forward();
  }

  void _pickCustom(LatLng pos) {
    // Snap to nearest landmark within 80m, else use typed label or "Custom Location"
    String label = widget.initialLabel.isNotEmpty
        ? widget.initialLabel
        : 'Custom Location';
    double nearest = double.infinity;
    _landmarks.forEach((name, latlng) {
      final d = const Distance().as(LengthUnit.Meter, latlng, pos);
      if (d < nearest) {
        nearest = d;
        if (d < 80) label = name;
      }
    });
    _pickLandmark(label, pos);
  }

  void _confirm() {
    if (_pickedLatLng == null) return;
    Navigator.pop(
      context,
      PickedLocation(label: _pickedLabel, latLng: _pickedLatLng!),
    );
  }

  List<MapEntry<String, LatLng>> get _filteredLandmarks {
    if (_searchQuery.isEmpty) return _landmarks.entries.toList();
    final q = _searchQuery.toLowerCase();
    return _landmarks.entries
        .where((e) => e.key.toLowerCase().contains(q))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).padding.bottom;

    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      appBar: _buildAppBar(),
      body: Stack(
        children: [
          // ── Map ──────────────────────────────────────────────────────────
          FlutterMap(
            mapController: _mapCtrl,
            options: MapOptions(
              initialCenter: _pickedLatLng ?? _collegeCentre,
              initialZoom: 16.5,
              minZoom: 10,
              maxZoom: 19,
              // Long-press to drop custom pin
              onLongPress: (_, pos) => _pickCustom(pos),
              onMapEvent: (evt) {
                // reserved for future drag-state handling
              },
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.campusassist.app',
                tileBuilder: _lightTileBuilder,
              ),
              if (_pickedLatLng != null)
                MarkerLayer(markers: [_buildPickedMarker()]),
              // Landmark dots
              MarkerLayer(
                markers: _landmarks.entries.map((e) {
                  final isSelected = e.key == _pickedLabel;
                  return Marker(
                    point: e.value,
                    width: 28,
                    height: 28,
                    child: GestureDetector(
                      onTap: () => _pickLandmark(e.key, e.value),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        decoration: BoxDecoration(
                          color: isSelected ? AppTheme.primary : Colors.white,
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: isSelected
                                ? AppTheme.primary
                                : AppTheme.divider,
                            width: 2,
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.15),
                              blurRadius: 4,
                            ),
                          ],
                        ),
                        child: Icon(
                          Icons.place_rounded,
                          size: 14,
                          color: isSelected
                              ? Colors.white
                              : AppTheme.textSecondary,
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ],
          ),

          // ── Top gradient ─────────────────────────────────────────────────
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: 130,
            child: IgnorePointer(
              child: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Colors.black54, Colors.transparent],
                  ),
                ),
              ),
            ),
          ),

          // ── Search + landmark chips ───────────────────────────────────────
          Positioned(
            top: MediaQuery.of(context).padding.top + 64,
            left: 12,
            right: 12,
            child: _SearchPanel(
              controller: _searchCtrl,
              query: _searchQuery,
              onChanged: (q) => setState(() => _searchQuery = q),
              onSearch: (q) {
                FocusScope.of(context).unfocus();
                _geocodeAndFly(q);
              },
              landmarks: _filteredLandmarks,
              selectedLabel: _pickedLabel,
              onSelect: _pickLandmark,
            ),
          ),

          // ── Long-press hint (shown until first pin) ───────────────────────
          if (_pickedLatLng == null)
            Center(
              child: IgnorePointer(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const SizedBox(height: 60),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 18,
                        vertical: 10,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.6),
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.touch_app_rounded,
                            color: Colors.white,
                            size: 16,
                          ),
                          SizedBox(width: 8),
                          Text(
                            'Tap a landmark or long-press to pin',
                            style: TextStyle(color: Colors.white, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

          // ── Zoom controls ─────────────────────────────────────────────────
          Positioned(
            right: 12,
            bottom: _pickedLatLng != null ? 230 : 80,
            child: Column(
              children: [
                _ZoomBtn(
                  icon: Icons.add_rounded,
                  onTap: () => _mapCtrl.move(
                    _mapCtrl.camera.center,
                    math.min(_mapCtrl.camera.zoom + 1, 19),
                  ),
                ),
                const SizedBox(height: 8),
                _ZoomBtn(
                  icon: Icons.remove_rounded,
                  onTap: () => _mapCtrl.move(
                    _mapCtrl.camera.center,
                    math.max(_mapCtrl.camera.zoom - 1, 10),
                  ),
                ),
              ],
            ),
          ),

          // ── Geocoding spinner ─────────────────────────────────────────────
          if (_geocoding)
            Positioned.fill(
              child: IgnorePointer(
                child: Container(
                  color: Colors.black38,
                  child: Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 14,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(14),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.15),
                            blurRadius: 16,
                          ),
                        ],
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: AppTheme.primary,
                            ),
                          ),
                          SizedBox(width: 12),
                          Text(
                            'Finding location…',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          if (_pickedLatLng != null)
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: SlideTransition(
                position: _sheetSlide,
                child: _ConfirmSheet(
                  label: _pickedLabel,
                  latLng: _pickedLatLng!,
                  bottomInset: bottomInset,
                  onClear: () {
                    setState(() {
                      _pickedLatLng = null;
                      _pickedLabel = '';
                    });
                    _sheetCtrl.reverse();
                  },
                  onConfirm: _confirm,
                ),
              ),
            ),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: Colors.transparent,
      elevation: 0,
      leading: GestureDetector(
        onTap: () => Navigator.pop(context),
        child: Container(
          margin: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.15),
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white24),
          ),
          child: const Icon(Icons.close_rounded, color: Colors.white, size: 20),
        ),
      ),
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Pick Location',
            style: TextStyle(
              color: Colors.white,
              fontSize: 17,
              fontWeight: FontWeight.w700,
            ),
          ),
          Text(
            widget.collegeName,
            style: const TextStyle(color: Colors.white70, fontSize: 11),
          ),
        ],
      ),
    );
  }

  Marker _buildPickedMarker() {
    return Marker(
      point: _pickedLatLng!,
      width: 60,
      height: 70,
      alignment: Alignment.bottomCenter,
      child: ScaleTransition(
        scale: Tween<double>(begin: 0.5, end: 1.0).animate(_pinAnim),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: AppTheme.primary,
                borderRadius: BorderRadius.circular(8),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.primary.withOpacity(0.4),
                    blurRadius: 8,
                  ),
                ],
              ),
              child: Text(
                _pickedLabel.length > 14
                    ? '${_pickedLabel.substring(0, 12)}…'
                    : _pickedLabel,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            CustomPaint(
              size: const Size(12, 6),
              painter: _TrianglePainter(AppTheme.primary),
            ),
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: AppTheme.primary,
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 2),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.primary.withOpacity(0.5),
                    blurRadius: 6,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _lightTileBuilder(
    BuildContext context,
    Widget tileWidget,
    TileImage tile,
  ) {
    return ColorFiltered(
      colorFilter: const ColorFilter.matrix([
        0.95,
        0,
        0,
        0,
        5,
        0,
        0.95,
        0,
        0,
        5,
        0,
        0,
        0.90,
        0,
        10,
        0,
        0,
        0,
        1,
        0,
      ]),
      child: tileWidget,
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Search panel
// ─────────────────────────────────────────────────────────────────────────────

class _SearchPanel extends StatelessWidget {
  final TextEditingController controller;
  final String query;
  final ValueChanged<String> onChanged;
  final ValueChanged<String> onSearch;
  final List<MapEntry<String, LatLng>> landmarks;
  final String selectedLabel;
  final void Function(String, LatLng) onSelect;

  const _SearchPanel({
    required this.controller,
    required this.query,
    required this.onChanged,
    required this.onSearch,
    required this.landmarks,
    required this.selectedLabel,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Search bar
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.12),
                blurRadius: 12,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: TextField(
            controller: controller,
            onChanged: onChanged,
            onSubmitted: onSearch,
            textInputAction: TextInputAction.search,
            style: const TextStyle(fontSize: 13, color: AppTheme.textPrimary),
            decoration: InputDecoration(
              hintText: 'Search campus locations…',
              hintStyle: const TextStyle(
                fontSize: 13,
                color: AppTheme.textLight,
              ),
              prefixIcon: const Icon(
                Icons.search_rounded,
                color: AppTheme.textLight,
                size: 20,
              ),
              suffixIcon: query.isNotEmpty
                  ? GestureDetector(
                      onTap: () {
                        controller.clear();
                        onChanged('');
                      },
                      child: const Icon(
                        Icons.close_rounded,
                        color: AppTheme.textLight,
                        size: 18,
                      ),
                    )
                  : null,
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
        ),
        // Landmark chips
        if (landmarks.isNotEmpty) ...[
          const SizedBox(height: 8),
          SizedBox(
            height: 36,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: landmarks.length,
              separatorBuilder: (_, __) => const SizedBox(width: 6),
              itemBuilder: (_, i) {
                final entry = landmarks[i];
                final isSelected = entry.key == selectedLabel;
                return GestureDetector(
                  onTap: () => onSelect(entry.key, entry.value),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 180),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: isSelected ? AppTheme.primary : Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 6,
                        ),
                      ],
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.place_rounded,
                          size: 12,
                          color: isSelected
                              ? Colors.white
                              : AppTheme.textSecondary,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          entry.key,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: isSelected
                                ? Colors.white
                                : AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Confirm sheet
// ─────────────────────────────────────────────────────────────────────────────

class _ConfirmSheet extends StatelessWidget {
  final String label;
  final LatLng latLng;
  final double bottomInset;
  final VoidCallback onClear;
  final VoidCallback onConfirm;

  const _ConfirmSheet({
    required this.label,
    required this.latLng,
    required this.bottomInset,
    required this.onClear,
    required this.onConfirm,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(12, 0, 12, 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.13),
            blurRadius: 24,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: Padding(
        padding: EdgeInsets.fromLTRB(20, 18, 20, 18 + bottomInset),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Drag handle
            Container(
              width: 36,
              height: 4,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: AppTheme.divider,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppTheme.primary.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.location_on_rounded,
                    color: AppTheme.primary,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        label,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${latLng.latitude.toStringAsFixed(5)}, '
                        '${latLng.longitude.toStringAsFixed(5)}',
                        style: const TextStyle(
                          fontSize: 10,
                          fontFamily: 'monospace',
                          color: AppTheme.textLight,
                        ),
                      ),
                    ],
                  ),
                ),
                // Clear button
                GestureDetector(
                  onTap: onClear,
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppTheme.surface,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppTheme.divider),
                    ),
                    child: const Icon(
                      Icons.close_rounded,
                      size: 16,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onConfirm,
                icon: const Icon(Icons.check_rounded, size: 18),
                label: const Text(
                  'Confirm Location',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                ),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

class _ZoomBtn extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  const _ZoomBtn({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: Colors.white,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.15),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Icon(icon, size: 20, color: AppTheme.textPrimary),
      ),
    );
  }
}

class _TrianglePainter extends CustomPainter {
  final Color color;
  const _TrianglePainter(this.color);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = color;
    final path = ui.Path()
      ..moveTo(0, 0)
      ..lineTo(size.width, 0)
      ..lineTo(size.width / 2, size.height)
      ..close();
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(_TrianglePainter old) => old.color != color;
}
