// lib/screens/create_post_screen.dart
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:marquee/marquee.dart';
import '../viewmodel/post_viewmodel.dart';
import '../theme/app_theme.dart';
import 'location_picker_screen.dart';

class CreatePostScreen extends ConsumerStatefulWidget {
  final String? communityId;
  final String? communityName;

  const CreatePostScreen({super.key, this.communityId, this.communityName});

  @override
  ConsumerState<CreatePostScreen> createState() => _CreatePostScreenState();
}

class _CreatePostScreenState extends ConsumerState<CreatePostScreen> {
  final _contentCtrl = TextEditingController();
  final _contentFocus = FocusNode();
  final _locationCtrl = TextEditingController();
  // bool _isAnonymous = true;
  bool _addLocation = false;
  bool _submitting = false;
  bool _showPreview = false;
  String _selectedCategory = 'general';
  PickedLocation? _pickedLocation;
  final _formKey = GlobalKey<FormState>();
  final ImagePicker _imagePicker = ImagePicker();
  final List<XFile> _attachments = [];

  // Upload progress: fileIndex → 0.0..1.0  (only populated while submitting)
  final Map<int, double> _uploadProgress = {};

  /// The index of the file currently being uploaded (-1 if none).
  int get _uploadingFileIndex =>
      _uploadProgress.isEmpty ? -1 : _uploadProgress.keys.last;

  @override
  void dispose() {
    _contentCtrl.dispose();
    _contentFocus.dispose();
    _locationCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickFromGallery() async {
    try {
      final images = await _imagePicker.pickMultiImage(imageQuality: 80);
      if (!mounted || images.isEmpty) return;

      setState(() {
        _attachments.addAll(images);
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not pick images: $e'),
          backgroundColor: AppTheme.events,
        ),
      );
    }
  }

  Future<void> _pickFromCamera() async {
    try {
      final image = await _imagePicker.pickImage(
        source: ImageSource.camera,
        imageQuality: 80,
      );
      if (!mounted || image == null) return;

      setState(() {
        _attachments.add(image);
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not open camera: $e'),
          backgroundColor: AppTheme.events,
        ),
      );
    }
  }

  void _removeAttachmentAt(int index) {
    setState(() {
      _attachments.removeAt(index);
    });
  }

  Future<void> _showAttachPhotoOptions() async {
    await showModalBottomSheet<void>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_library_outlined),
              title: const Text('Choose from Gallery'),
              onTap: () {
                Navigator.pop(ctx);
                _pickFromGallery();
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_camera_outlined),
              title: const Text('Take a Photo'),
              onTap: () {
                Navigator.pop(ctx);
                _pickFromCamera();
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (widget.communityId == null || widget.communityId!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No community selected for this post.')),
      );
      return;
    }
    setState(() {
      _submitting = true;
      _uploadProgress.clear();
    });
    try {
      await ref
          .read(postListProvider(widget.communityId!).notifier)
          .createPost(
            content: _contentCtrl.text.trim(),
            category: _selectedCategory,
            locationLabel: _pickedLocation?.label,
            locationLat: _pickedLocation?.latLng.latitude,
            locationLng: _pickedLocation?.latLng.longitude,
            attachments: _attachments,
            onFileProgress: (fileIndex, sent, total) {
              if (!mounted) return;
              setState(() {
                _uploadProgress[fileIndex] = total > 0 ? sent / total : 0.0;
              });
            },
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Row(
              children: [
                Icon(Icons.check_circle_rounded, color: Colors.white),
                SizedBox(width: 8),
                Text('Post created successfully!'),
              ],
            ),
            backgroundColor: AppTheme.success,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        );
        Navigator.pop(context, true);
      }
    } catch (e) {
      setState(() {
        _submitting = false;
        _uploadProgress.clear();
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString().replaceFirst('Exception: ', '')),
          backgroundColor: AppTheme.events,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final communityName = widget.communityName;
    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(
        title: const Text('Ask a Question'),
        leading: IconButton(
          icon: const Icon(Icons.close_rounded),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ElevatedButton(
              onPressed: _submitting ? null : _submit,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 8,
                ),
              ),
              child: _submitting
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 2,
                      ),
                    )
                  : const Text('Post'),
            ),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Community badge
              if (communityName != null)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: AppTheme.primary.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.people_rounded,
                        size: 14,
                        color: AppTheme.primary,
                      ),
                      const SizedBox(width: 6),
                      Flexible(
                        child: SizedBox(
                          height: 20,
                          child: Marquee(
                            text: 'Posting to: $communityName',
                            style: const TextStyle(
                              fontSize: 13,
                              color: AppTheme.primary,
                              fontWeight: FontWeight.w600,
                            ),
                            scrollAxis: Axis.horizontal,
                            crossAxisAlignment: CrossAxisAlignment.center,
                            blankSpace:
                                20.0, // Space between the end of text and start of next cycle
                            velocity: 30.0, // Pixels per second
                            pauseAfterRound: const Duration(seconds: 1),
                            accelerationDuration: const Duration(seconds: 1),
                            accelerationCurve: Curves.linear,
                            decelerationDuration: const Duration(
                              milliseconds: 500,
                            ),
                            decelerationCurve: Curves.easeOut,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 20),

              // ── Category picker ──────────────────────────────────────────
              const Text(
                'Category',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              SizedBox(
                height: 36,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children:
                      [
                        'general',
                        'academics',
                        'hostel',
                        'facilities',
                        'food',
                        'career',
                        'events',
                      ].map((cat) {
                        final selected = _selectedCategory == cat;
                        final label = cat[0].toUpperCase() + cat.substring(1);
                        return GestureDetector(
                          onTap: () => setState(() => _selectedCategory = cat),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 160),
                            margin: const EdgeInsets.only(right: 8),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 14,
                              vertical: 7,
                            ),
                            decoration: BoxDecoration(
                              color: selected ? AppTheme.primary : Colors.white,
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: selected
                                    ? AppTheme.primary
                                    : AppTheme.divider,
                              ),
                            ),
                            child: Text(
                              label,
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: selected
                                    ? Colors.white
                                    : AppTheme.textSecondary,
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                ),
              ),
              const SizedBox(height: 20),

              // Content — markdown editor / preview
              Row(
                children: [
                  const Text(
                    'Description *',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const Spacer(),
                  // Write / Preview toggle
                  Container(
                    decoration: BoxDecoration(
                      color: AppTheme.surface,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppTheme.divider),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _TabBtn(
                          label: 'Write',
                          active: !_showPreview,
                          onTap: () => setState(() => _showPreview = false),
                        ),
                        _TabBtn(
                          label: 'Preview',
                          active: _showPreview,
                          onTap: () {
                            _contentFocus.unfocus();
                            setState(() => _showPreview = true);
                          },
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              if (!_showPreview) ...[
                // ── Markdown toolbar ──────────────────────────────────────
                _MarkdownToolbar(
                  controller: _contentCtrl,
                  focusNode: _contentFocus,
                ),
                const SizedBox(height: 4),
                // ── Editor ───────────────────────────────────────────────
                TextFormField(
                  controller: _contentCtrl,
                  focusNode: _contentFocus,
                  decoration: InputDecoration(
                    hintText:
                        'What do you want to share or ask?\n\nSupports **bold**, *italic*, # headings, - lists, `code`…',
                    hintStyle: const TextStyle(
                      fontSize: 13,
                      color: AppTheme.textLight,
                    ),
                    alignLabelWithHint: true,
                    border: const OutlineInputBorder(
                      borderRadius: BorderRadius.vertical(
                        bottom: Radius.circular(10),
                      ),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: const BorderRadius.vertical(
                        bottom: Radius.circular(10),
                      ),
                      borderSide: BorderSide(color: AppTheme.divider),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: const BorderRadius.vertical(
                        bottom: Radius.circular(10),
                      ),
                      borderSide: BorderSide(
                        color: AppTheme.primary,
                        width: 1.5,
                      ),
                    ),
                    errorBorder: OutlineInputBorder(
                      borderRadius: const BorderRadius.vertical(
                        bottom: Radius.circular(10),
                      ),
                      borderSide: BorderSide(color: AppTheme.events),
                    ),
                    focusedErrorBorder: OutlineInputBorder(
                      borderRadius: const BorderRadius.vertical(
                        bottom: Radius.circular(10),
                      ),
                      borderSide: BorderSide(
                        color: AppTheme.events,
                        width: 1.5,
                      ),
                    ),
                  ),
                  maxLines: 10,
                  minLines: 6,
                  maxLength: 2000,
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 13.5,
                    height: 1.55,
                    color: AppTheme.textPrimary,
                  ),
                  onChanged: (_) => setState(() {}),
                  validator: (v) => (v == null || v.trim().isEmpty)
                      ? 'Description is required'
                      : null,
                ),
              ] else ...[
                // ── Preview ───────────────────────────────────────────────
                Container(
                  width: double.infinity,
                  constraints: const BoxConstraints(minHeight: 160),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.divider),
                  ),
                  child: _contentCtrl.text.trim().isEmpty
                      ? const Text(
                          'Nothing to preview yet.',
                          style: TextStyle(
                            color: AppTheme.textLight,
                            fontSize: 13,
                            fontStyle: FontStyle.italic,
                          ),
                        )
                      : MarkdownBody(
                          data: _contentCtrl.text,
                          selectable: true,
                          styleSheet:
                              MarkdownStyleSheet.fromTheme(
                                Theme.of(context),
                              ).copyWith(
                                p: const TextStyle(
                                  fontSize: 14,
                                  height: 1.55,
                                  color: AppTheme.textPrimary,
                                ),
                                code: TextStyle(
                                  fontFamily: 'monospace',
                                  fontSize: 12.5,
                                  backgroundColor: AppTheme.surface,
                                  color: AppTheme.primary,
                                ),
                                codeblockDecoration: BoxDecoration(
                                  color: AppTheme.surface,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: AppTheme.divider),
                                ),
                                blockquoteDecoration: BoxDecoration(
                                  border: Border(
                                    left: BorderSide(
                                      color: AppTheme.primary.withOpacity(0.5),
                                      width: 3,
                                    ),
                                  ),
                                ),
                              ),
                        ),
                ),
              ],
              const SizedBox(height: 16),

              // Attach photos
              const Text(
                'Attachments',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: _showAttachPhotoOptions,
                icon: const Icon(
                  Icons.add_a_photo_outlined,
                  size: 18,
                  color: AppTheme.primary,
                ),
                label: const Text(
                  'Attach Photos',
                  style: TextStyle(
                    color: AppTheme.primary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 46),
                  side: BorderSide(color: AppTheme.primary.withOpacity(0.3)),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
              ),
              if (_attachments.isNotEmpty) ...[
                const SizedBox(height: 10),
                Row(
                  children: [
                    Text(
                      '${_attachments.length} photo(s) attached',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppTheme.textSecondary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (_submitting && _uploadingFileIndex >= 0) ...[
                      const SizedBox(width: 8),
                      Text(
                        'Uploading ${_uploadingFileIndex + 1}/${_attachments.length}…',
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppTheme.primary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 8),
                SizedBox(
                  height: 92,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: _attachments.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 10),
                    itemBuilder: (_, i) {
                      final img = _attachments[i];
                      final progress = _uploadProgress[i];
                      final isUploading =
                          _submitting && _uploadingFileIndex == i;
                      final isDone =
                          _submitting && (_uploadProgress[i] ?? 0) >= 1.0;
                      return Stack(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(10),
                            child: FutureBuilder<Uint8List>(
                              future: img.readAsBytes(),
                              builder: (_, snapshot) {
                                if (snapshot.hasData) {
                                  return Image.memory(
                                    snapshot.data!,
                                    width: 92,
                                    height: 92,
                                    fit: BoxFit.cover,
                                  );
                                }
                                return Container(
                                  width: 92,
                                  height: 92,
                                  color: AppTheme.surface,
                                  child: const Center(
                                    child: SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
                          // Upload progress overlay
                          if (isUploading || (isDone))
                            Positioned.fill(
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(10),
                                child: Container(
                                  color: Colors.black.withOpacity(0.45),
                                  alignment: Alignment.center,
                                  child: isDone
                                      ? const Icon(
                                          Icons.check_circle_rounded,
                                          color: Colors.white,
                                          size: 26,
                                        )
                                      : SizedBox(
                                          width: 36,
                                          height: 36,
                                          child: CircularProgressIndicator(
                                            value: progress,
                                            strokeWidth: 3,
                                            color: Colors.white,
                                            backgroundColor: Colors.white
                                                .withOpacity(0.3),
                                          ),
                                        ),
                                ),
                              ),
                            ),
                          // Remove button — hidden while submitting
                          if (!_submitting)
                            Positioned(
                              top: 4,
                              right: 4,
                              child: GestureDetector(
                                onTap: () => _removeAttachmentAt(i),
                                child: Container(
                                  width: 22,
                                  height: 22,
                                  decoration: BoxDecoration(
                                    color: Colors.black.withOpacity(0.6),
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(
                                    Icons.close_rounded,
                                    size: 14,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                            ),
                        ],
                      );
                    },
                  ),
                ),
              ],
              const SizedBox(height: 16),

              // Location section
              AnimatedContainer(
                duration: const Duration(milliseconds: 220),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: _pickedLocation != null
                        ? AppTheme.primary.withOpacity(0.4)
                        : AppTheme.divider,
                    width: _pickedLocation != null ? 1.5 : 1,
                  ),
                  boxShadow: _pickedLocation != null
                      ? [
                          BoxShadow(
                            color: AppTheme.primary.withOpacity(0.07),
                            blurRadius: 12,
                            offset: const Offset(0, 2),
                          ),
                        ]
                      : [],
                ),
                child: Column(
                  children: [
                    // Toggle
                    SwitchListTile(
                      value: _addLocation,
                      onChanged: (v) => setState(() {
                        _addLocation = v;
                        if (!v) {
                          _pickedLocation = null;
                          _locationCtrl.clear();
                        }
                      }),
                      title: const Text(
                        'Add Campus Location',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      subtitle: const Text(
                        'Tag a specific spot on campus',
                        style: TextStyle(fontSize: 12),
                      ),
                      secondary: const Icon(
                        Icons.location_on_rounded,
                        color: AppTheme.primary,
                      ),
                      activeColor: AppTheme.primary,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 4,
                      ),
                    ),
                    if (_addLocation) ...[
                      const Divider(height: 1, indent: 16, endIndent: 16),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Text field — always visible
                            TextFormField(
                              controller: _locationCtrl,
                              onChanged: (_) {
                                // Rebuild so button text/style updates live
                                setState(() {
                                  if (_pickedLocation != null) {
                                    _pickedLocation = null;
                                  }
                                });
                              },
                              decoration: const InputDecoration(
                                hintText:
                                    'e.g. Block C Hostel, Main Canteen...',
                                prefixIcon: Icon(
                                  Icons.place_rounded,
                                  color: AppTheme.textLight,
                                ),
                              ),
                            ),
                            const SizedBox(height: 10),

                            // Map button — text changes based on field content
                            GestureDetector(
                              onTap: _locationCtrl.text.trim().isEmpty
                                  ? null
                                  : () async {
                                      final result =
                                          await Navigator.push<PickedLocation>(
                                            context,
                                            MaterialPageRoute(
                                              builder: (_) =>
                                                  LocationPickerScreen(
                                                    collegeId:
                                                        widget.communityId ??
                                                        '',
                                                    collegeName:
                                                        widget.communityName ??
                                                        '',
                                                    initialLabel: _locationCtrl
                                                        .text
                                                        .trim(),
                                                    initial: _pickedLocation,
                                                  ),
                                            ),
                                          );
                                      if (result != null && mounted) {
                                        setState(() {
                                          _pickedLocation = result;
                                          _locationCtrl.text = result.label;
                                        });
                                      } else if (result == null && mounted) {
                                        ScaffoldMessenger.of(
                                          context,
                                        ).showSnackBar(
                                          SnackBar(
                                            content: Row(
                                              children: [
                                                const Icon(
                                                  Icons.location_off_rounded,
                                                  color: Colors.white,
                                                  size: 16,
                                                ),
                                                const SizedBox(width: 8),
                                                Text(
                                                  'Could not find "${_locationCtrl.text.trim()}" on the map',
                                                ),
                                              ],
                                            ),
                                            backgroundColor: AppTheme.events,
                                            behavior: SnackBarBehavior.floating,
                                            shape: RoundedRectangleBorder(
                                              borderRadius:
                                                  BorderRadius.circular(10),
                                            ),
                                          ),
                                        );
                                      }
                                    },
                              child: AnimatedContainer(
                                duration: const Duration(milliseconds: 200),
                                width: double.infinity,
                                padding: const EdgeInsets.symmetric(
                                  vertical: 12,
                                ),
                                decoration: BoxDecoration(
                                  color: _locationCtrl.text.trim().isEmpty
                                      ? AppTheme.surface
                                      : AppTheme.primary.withOpacity(0.06),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(
                                    color: _locationCtrl.text.trim().isEmpty
                                        ? AppTheme.divider
                                        : AppTheme.primary.withOpacity(0.3),
                                  ),
                                ),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(
                                      _locationCtrl.text.trim().isEmpty
                                          ? Icons.search_rounded
                                          : Icons.map_rounded,
                                      size: 15,
                                      color: _locationCtrl.text.trim().isEmpty
                                          ? AppTheme.textLight
                                          : AppTheme.primary,
                                    ),
                                    const SizedBox(width: 7),
                                    Text(
                                      _locationCtrl.text.trim().isEmpty
                                          ? 'Enter a location to find on map'
                                          : 'Pick on Map',
                                      style: TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.w600,
                                        color: _locationCtrl.text.trim().isEmpty
                                            ? AppTheme.textLight
                                            : AppTheme.primary,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),

                            // Pin confirmed preview — shown only after picking
                            if (_pickedLocation != null) ...[
                              const SizedBox(height: 10),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 8,
                                ),
                                decoration: BoxDecoration(
                                  color: AppTheme.success.withOpacity(0.07),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(
                                    color: AppTheme.success.withOpacity(0.3),
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    const Icon(
                                      Icons.check_circle_rounded,
                                      size: 16,
                                      color: AppTheme.success,
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          const Text(
                                            'Location pinned on map',
                                            style: TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.w600,
                                              color: AppTheme.success,
                                            ),
                                          ),
                                          Text(
                                            '${_pickedLocation!.latLng.latitude.toStringAsFixed(5)}, '
                                            '${_pickedLocation!.latLng.longitude.toStringAsFixed(5)}',
                                            style: const TextStyle(
                                              fontSize: 10,
                                              fontFamily: 'monospace',
                                              color: AppTheme.textLight,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    GestureDetector(
                                      onTap: () => setState(
                                        () => _pickedLocation = null,
                                      ),
                                      child: const Icon(
                                        Icons.close_rounded,
                                        size: 16,
                                        color: AppTheme.textSecondary,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 12),

              // Anonymous toggle
              // Container(
              //   decoration: BoxDecoration(
              //     color: Colors.white,
              //     borderRadius: BorderRadius.circular(12),
              //     border: Border.all(color: AppTheme.divider),
              //   ),
              //   child: SwitchListTile(
              //     value: _isAnonymous,
              //     onChanged: (v) => setState(() => _isAnonymous = v),
              //     title: const Text(
              //       'Post Anonymously',
              //       style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
              //     ),
              //     subtitle: const Text(
              //       'Your identity will be hidden',
              //       style: TextStyle(fontSize: 12),
              //     ),
              //     secondary: const Icon(
              //       Icons.shield_outlined,
              //       color: AppTheme.success,
              //     ),
              //     activeColor: AppTheme.success,
              //     contentPadding: const EdgeInsets.symmetric(
              //       horizontal: 16,
              //       vertical: 4,
              //     ),
              //   ),
              // ),
              // const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Write/Preview tab button ───────────────────────────────────────────────────

class _TabBtn extends StatelessWidget {
  final String label;
  final bool active;
  final VoidCallback onTap;

  const _TabBtn({
    required this.label,
    required this.active,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        decoration: BoxDecoration(
          color: active ? AppTheme.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(7),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: active ? Colors.white : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }
}

// ── Markdown formatting toolbar ────────────────────────────────────────────────

class _MarkdownToolbar extends StatelessWidget {
  final TextEditingController controller;
  final FocusNode focusNode;

  const _MarkdownToolbar({required this.controller, required this.focusNode});

  void _wrap(String before, String after) {
    final text = controller.text;
    final sel = controller.selection;
    final selectedText = sel.isValid && sel.start != sel.end
        ? text.substring(sel.start, sel.end)
        : '';
    final replacement = '$before$selectedText$after';
    final newText = text.replaceRange(
      sel.isValid ? sel.start : text.length,
      sel.isValid ? sel.end : text.length,
      replacement,
    );
    final cursorPos =
        (sel.isValid ? sel.start : text.length) +
        before.length +
        selectedText.length +
        after.length;
    controller.value = TextEditingValue(
      text: newText,
      selection: TextSelection.collapsed(offset: cursorPos),
    );
    focusNode.requestFocus();
  }

  void _insertLine(String prefix) {
    final text = controller.text;
    final sel = controller.selection;
    final pos = sel.isValid ? sel.start : text.length;
    // Find start of line
    final lineStart = text.lastIndexOf('\n', pos - 1) + 1;
    final lineText = text.substring(lineStart, pos);
    // If already starts with prefix, remove it; otherwise prepend
    String newText;
    int newPos;
    if (lineText.startsWith(prefix)) {
      newText = text.replaceRange(lineStart, lineStart + prefix.length, '');
      newPos = pos - prefix.length;
    } else {
      newText = text.replaceRange(lineStart, lineStart, prefix);
      newPos = pos + prefix.length;
    }
    controller.value = TextEditingValue(
      text: newText,
      selection: TextSelection.collapsed(offset: newPos),
    );
    focusNode.requestFocus();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 40,
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppTheme.divider),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(10)),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 6),
        child: Row(
          children: [
            _ToolbarBtn(
              icon: Icons.format_bold,
              tooltip: 'Bold',
              onTap: () => _wrap('**', '**'),
            ),
            _ToolbarBtn(
              icon: Icons.format_italic,
              tooltip: 'Italic',
              onTap: () => _wrap('*', '*'),
            ),
            _ToolbarBtn(
              icon: Icons.format_strikethrough,
              tooltip: 'Strikethrough',
              onTap: () => _wrap('~~', '~~'),
            ),
            const _ToolbarDivider(),
            _ToolbarBtn(
              icon: Icons.title_rounded,
              tooltip: 'Heading',
              onTap: () => _insertLine('## '),
            ),
            _ToolbarBtn(
              icon: Icons.format_list_bulleted,
              tooltip: 'Bullet list',
              onTap: () => _insertLine('- '),
            ),
            _ToolbarBtn(
              icon: Icons.format_list_numbered,
              tooltip: 'Numbered list',
              onTap: () => _insertLine('1. '),
            ),
            _ToolbarBtn(
              icon: Icons.format_quote_rounded,
              tooltip: 'Quote',
              onTap: () => _insertLine('> '),
            ),
            const _ToolbarDivider(),
            _ToolbarBtn(
              icon: Icons.code_rounded,
              tooltip: 'Inline code',
              onTap: () => _wrap('`', '`'),
            ),
            _ToolbarBtn(
              icon: Icons.integration_instructions_outlined,
              tooltip: 'Code block',
              onTap: () => _wrap('\n```\n', '\n```\n'),
            ),
            const _ToolbarDivider(),
            _ToolbarBtn(
              icon: Icons.link_rounded,
              tooltip: 'Link',
              onTap: () => _wrap('[', '](url)'),
            ),
          ],
        ),
      ),
    );
  }
}

class _ToolbarBtn extends StatelessWidget {
  final IconData icon;
  final String tooltip;
  final VoidCallback onTap;

  const _ToolbarBtn({
    required this.icon,
    required this.tooltip,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(6),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          child: Icon(icon, size: 18, color: AppTheme.textSecondary),
        ),
      ),
    );
  }
}

class _ToolbarDivider extends StatelessWidget {
  const _ToolbarDivider();

  @override
  Widget build(BuildContext context) => Container(
    width: 1,
    height: 20,
    color: AppTheme.divider,
    margin: const EdgeInsets.symmetric(horizontal: 4),
  );
}
