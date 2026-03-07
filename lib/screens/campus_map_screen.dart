// lib/screens/campus_map_screen.dart
//
// Uses flutter_map + latlong2 (no API key required – OpenStreetMap tiles).
// Geocodes the location label via Nominatim when not found in campus_locations.

import 'dart:math' as math;
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../data/campus_locations.dart';

// ─────────────────────────────────────────────────────────────────────────────

class CampusMapScreen extends StatefulWidget {
  final String collegeId;
  final String collegeName;
  final String? locationLabel;
  final double? locationLat;
  final double? locationLng;
  final String postTitle;

  const CampusMapScreen({
    super.key,
    required this.collegeId,
    required this.collegeName,
    required this.locationLabel,
    this.locationLat,
    this.locationLng,
    required this.postTitle,
  });

  @override
  State<CampusMapScreen> createState() => _CampusMapScreenState();
}

class _CampusMapScreenState extends State<CampusMapScreen>
    with TickerProviderStateMixin {
  late final MapController _mapCtrl;
  late final AnimationController _pulseCtrl;
  late final AnimationController _cardCtrl;
  late final Animation<double> _pulseAnim;
  late final Animation<Offset> _cardSlide;
  late final Animation<double> _cardFade;

  // The resolved pin – starts at the known fallback, updated after geocode
  late LatLng _pinLocation;
  String _resolvedLabel = '';
  bool _geocoding = false;
  bool _satelliteMode = false;
  double _currentZoom = 17.0;

  // Search
  final _searchCtrl = TextEditingController();
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _mapCtrl = MapController();

    // Use exact coordinates if available (stored when user picked on map)
    if (widget.locationLat != null && widget.locationLng != null) {
      _pinLocation = LatLng(widget.locationLat!, widget.locationLng!);
    } else {
      // Best-effort from the static table
      _pinLocation = resolveLocation(widget.collegeId, widget.locationLabel);
    }
    _resolvedLabel = widget.locationLabel ?? 'Campus Location';

    // Pulse animation for the pin ring
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    )..repeat();
    _pulseAnim = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeOut));

    // Bottom card slide-up
    _cardCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );
    _cardSlide = Tween<Offset>(
      begin: const Offset(0, 1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _cardCtrl, curve: Curves.easeOutCubic));
    _cardFade = CurvedAnimation(parent: _cardCtrl, curve: Curves.easeOut);

    Future.delayed(const Duration(milliseconds: 300), () {
      if (mounted) _cardCtrl.forward();
    });

    // Geocode the label only when we have no exact coordinates
    // and the static table also didn't find a match
    if (widget.locationLat == null &&
        widget.locationLabel != null &&
        widget.locationLabel!.isNotEmpty &&
        _pinLocation == const LatLng(20.5937, 78.9629)) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _geocodeLabel(widget.locationLabel!);
      });
    }
  }

  /// Geocodes [query] via Nominatim, biased towards the college location.
  /// Geocodes [query] via Nominatim, biased towards the college location.
  Future<void> _geocodeLabel(String query) async {
    if (!mounted) return;
    setState(() => _geocoding = true);

    final collegeCentre =
        collegeCentres[widget.collegeId] ?? const LatLng(20.5937, 78.9629);

    // 1. Check campus landmark map
    final landmarks = campusLocations[widget.collegeId] ?? {};
    final q = query.toLowerCase().trim();
    for (final entry in landmarks.entries) {
      if (entry.key.toLowerCase() == q || entry.key.toLowerCase().contains(q)) {
        if (mounted) {
          setState(() {
            _pinLocation = entry.value; // ← was wrongly using undefined `pos`
            _resolvedLabel = entry.key; // ← use matched landmark name
            _geocoding = false;
          });
          _mapCtrl.move(entry.value, 17.0);
        }
        return;
      }
    }

    // 2. Nominatim
    try {
      final dio = Dio(
        BaseOptions(
          headers: {'User-Agent': 'CampusAssist/1.0'},
          connectTimeout: const Duration(seconds: 8),
          receiveTimeout: const Duration(seconds: 8),
        ),
      );
      final response = await dio.get<List<dynamic>>(
        'https://nominatim.openstreetmap.org/search',
        queryParameters: {
          'q': '$query, ${widget.collegeName}, India',
          'format': 'json',
          'limit': '1',
          'viewbox':
              '${collegeCentre.longitude - 0.1},${collegeCentre.latitude + 0.1},'
              '${collegeCentre.longitude + 0.1},${collegeCentre.latitude - 0.1}',
          'bounded': '0',
        },
      );

      final results = response.data ?? [];
      if (results.isNotEmpty && mounted) {
        final lat = double.parse(results[0]['lat'] as String);
        final lon = double.parse(results[0]['lon'] as String);
        final pos = LatLng(lat, lon);
        setState(() {
          _pinLocation = pos;
          _resolvedLabel = query; // ← was missing, label never updated
          _geocoding = false;
        });
        _mapCtrl.move(pos, 17.0); // ← was _pinLocation (stale), now uses pos
        return;
      }
    } on DioException {
      // Fall through
    }

    // 3. Fallback: fly to college centre
    if (mounted) {
      setState(() {
        _pinLocation = collegeCentre;
        _resolvedLabel = query; // ← was missing
        _geocoding = false;
      });
      _mapCtrl.move(collegeCentre, 16.5);
    }
  }

  /// Geocodes a search query entered by the user and moves the pin.
  // ✅ AFTER — just remove the trailing setState; _geocodeLabel now handles it
  Future<void> _searchLocation(String query) async {
    final q = query.trim();
    if (q.isEmpty) return;
    FocusScope.of(context).unfocus();
    await _geocodeLabel(q);
    // _resolvedLabel is already set inside _geocodeLabel
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    _cardCtrl.dispose();
    _mapCtrl.dispose();
    _searchCtrl.dispose();
    super.dispose();
  }

  void _zoomIn() {
    _currentZoom = math.min(_currentZoom + 1, 19);
    _mapCtrl.move(_mapCtrl.camera.center, _currentZoom);
  }

  void _zoomOut() {
    _currentZoom = math.max(_currentZoom - 1, 10);
    _mapCtrl.move(_mapCtrl.camera.center, _currentZoom);
  }

  void _centreOnPin() {
    _mapCtrl.move(_pinLocation, 17.0);
    _currentZoom = 17.0;
  }

  Future<void> _openInGoogleMaps() async {
    final uri = Uri.parse(
      'https://maps.google.com/?q=${_pinLocation.latitude},${_pinLocation.longitude}',
    );
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open Google Maps')),
        );
      }
    }
  }

  String get _tileUrl => _satelliteMode
      ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
      : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

  @override
  Widget build(BuildContext context) {
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
              initialCenter: _pinLocation,
              initialZoom: _currentZoom,
              minZoom: 10,
              maxZoom: 19,
              onMapEvent: (evt) {
                if (evt is MapEventMove) {
                  setState(() => _currentZoom = evt.camera.zoom);
                }
              },
            ),
            children: [
              TileLayer(
                urlTemplate: _tileUrl,
                userAgentPackageName: 'com.campusassist.app',
                tileBuilder: _satelliteMode ? null : _lightTileBuilder,
              ),
              MarkerLayer(markers: [_buildMarker()]),
            ],
          ),

          // ── Top gradient fade ─────────────────────────────────────────────
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

          // ── Search bar (below app bar) ────────────────────────────────────
          Positioned(
            top: MediaQuery.of(context).padding.top + 62,
            left: 12,
            right: 12,
            child: _buildSearchBar(),
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

          // ── Zoom & locate controls ────────────────────────────────────────
          Positioned(
            right: 16,
            bottom: 220,
            child: Column(
              children: [
                _MapButton(
                  icon: Icons.add_rounded,
                  onTap: _zoomIn,
                  tooltip: 'Zoom in',
                ),
                const SizedBox(height: 8),
                _MapButton(
                  icon: Icons.remove_rounded,
                  onTap: _zoomOut,
                  tooltip: 'Zoom out',
                ),
                const SizedBox(height: 8),
                _MapButton(
                  icon: Icons.my_location_rounded,
                  onTap: _centreOnPin,
                  tooltip: 'Centre on location',
                  highlight: true,
                ),
              ],
            ),
          ),

          // ── Layer toggle ──────────────────────────────────────────────────
          Positioned(
            right: 16,
            bottom: 390,
            child: _MapButton(
              icon: _satelliteMode
                  ? Icons.map_rounded
                  : Icons.satellite_alt_rounded,
              onTap: () => setState(() => _satelliteMode = !_satelliteMode),
              tooltip: _satelliteMode ? 'Street map' : 'Satellite',
            ),
          ),

          // ── Bottom info card ──────────────────────────────────────────────
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: SlideTransition(
              position: _cardSlide,
              child: FadeTransition(
                opacity: _cardFade,
                child: _LocationCard(
                  locationLabel: _resolvedLabel,
                  collegeName: widget.collegeName,
                  postTitle: widget.postTitle,
                  pinLocation: _pinLocation,
                  onOpenMaps: _openInGoogleMaps,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.18),
            blurRadius: 14,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: TextField(
        controller: _searchCtrl,
        onChanged: (v) => setState(() => _searchQuery = v),
        onSubmitted: _searchLocation,
        textInputAction: TextInputAction.search,
        style: const TextStyle(fontSize: 13, color: AppTheme.textPrimary),
        decoration: InputDecoration(
          hintText: 'Search location on map…',
          hintStyle: const TextStyle(fontSize: 13, color: AppTheme.textLight),
          prefixIcon: const Icon(
            Icons.search_rounded,
            color: AppTheme.textLight,
            size: 20,
          ),
          suffixIcon: _searchQuery.isNotEmpty
              ? GestureDetector(
                  onTap: () {
                    _searchCtrl.clear();
                    setState(() => _searchQuery = '');
                  },
                  child: const Icon(
                    Icons.close_rounded,
                    color: AppTheme.textLight,
                    size: 18,
                  ),
                )
              : GestureDetector(
                  onTap: () => _searchLocation(_searchCtrl.text),
                  child: const Icon(
                    Icons.arrow_forward_rounded,
                    color: AppTheme.primary,
                    size: 18,
                  ),
                ),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(vertical: 14),
        ),
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
          child: const Icon(
            Icons.arrow_back_ios_new_rounded,
            color: Colors.white,
            size: 18,
          ),
        ),
      ),
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Campus Map',
            style: TextStyle(
              color: Colors.white,
              fontSize: 17,
              fontWeight: FontWeight.w700,
            ),
          ),
          Text(
            widget.collegeName,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 11,
              fontWeight: FontWeight.w400,
            ),
          ),
        ],
      ),
    );
  }

  Marker _buildMarker() {
    return Marker(
      point: _pinLocation,
      width: 80,
      height: 80,
      child: AnimatedBuilder(
        animation: _pulseAnim,
        builder: (_, __) {
          final scale = 1.0 + (_pulseAnim.value * 0.9);
          final opacity = (1.0 - _pulseAnim.value).clamp(0.0, 1.0);
          return Stack(
            alignment: Alignment.center,
            children: [
              Transform.scale(
                scale: scale,
                child: Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: AppTheme.primary.withOpacity(opacity * 0.6),
                      width: 2,
                    ),
                    color: AppTheme.primary.withOpacity(opacity * 0.15),
                  ),
                ),
              ),
              Container(
                width: 20,
                height: 20,
                decoration: BoxDecoration(
                  color: AppTheme.primary,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 3),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primary.withOpacity(0.5),
                      blurRadius: 8,
                      spreadRadius: 1,
                    ),
                  ],
                ),
              ),
            ],
          );
        },
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

class _LocationCard extends StatelessWidget {
  final String locationLabel;
  final String collegeName;
  final String postTitle;
  final LatLng pinLocation;
  final VoidCallback onOpenMaps;

  const _LocationCard({
    required this.locationLabel,
    required this.collegeName,
    required this.postTitle,
    required this.pinLocation,
    required this.onOpenMaps,
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
            color: Colors.black.withOpacity(0.12),
            blurRadius: 24,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Drag handle
          Padding(
            padding: const EdgeInsets.only(top: 10),
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: AppTheme.divider,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 14, 20, 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Location name row
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(9),
                      decoration: BoxDecoration(
                        color: AppTheme.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.location_on_rounded,
                        color: AppTheme.primary,
                        size: 20,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            locationLabel.isEmpty
                                ? 'Campus Location'
                                : locationLabel,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                          Text(
                            collegeName,
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Coords badge
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: AppTheme.surface,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppTheme.divider),
                      ),
                      child: Text(
                        '${pinLocation.latitude.toStringAsFixed(4)}, '
                        '${pinLocation.longitude.toStringAsFixed(4)}',
                        style: const TextStyle(
                          fontSize: 9,
                          fontFamily: 'monospace',
                          color: AppTheme.textLight,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                // Post context
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.surface,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.divider),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.chat_bubble_outline_rounded,
                        size: 14,
                        color: AppTheme.textSecondary,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          postTitle,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppTheme.textSecondary,
                            height: 1.4,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),
                // Open in external maps
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: onOpenMaps,
                    icon: const Icon(Icons.open_in_new_rounded, size: 15),
                    label: const Text('Open in Google Maps'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.primary,
                      side: const BorderSide(color: AppTheme.primary),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: MediaQuery.of(context).padding.bottom),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────

class _MapButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final String tooltip;
  final bool highlight;

  const _MapButton({
    required this.icon,
    required this.onTap,
    required this.tooltip,
    this.highlight = false,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: highlight ? AppTheme.primary : Colors.white,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.15),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Icon(
            icon,
            size: 20,
            color: highlight ? Colors.white : AppTheme.textPrimary,
          ),
        ),
      ),
    );
  }
}
