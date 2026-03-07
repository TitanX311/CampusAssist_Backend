// lib/widgets/category_filter.dart
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class CategoryFilter extends StatelessWidget {
  final String selected;
  final ValueChanged<String> onChanged;

  static const List<String> categories = [
    'All',
    'Academics',
    'Hostel',
    'Facilities',
    'Food',
    'Career',
    'Events',
    'General',
  ];

  const CategoryFilter({
    super.key,
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 44,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: categories.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, i) {
          final cat = categories[i];
          final isSelected = cat == selected;
          final color = cat == 'All'
              ? AppTheme.primary
              : AppTheme.categoryColor(cat);
          return GestureDetector(
            onTap: () => onChanged(cat),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: isSelected ? color : Colors.white,
                borderRadius: BorderRadius.circular(22),
                border: Border.all(
                  color: isSelected ? color : AppTheme.divider,
                ),
                boxShadow: isSelected
                    ? [BoxShadow(color: color.withOpacity(0.25), blurRadius: 8)]
                    : [],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (cat != 'All') ...[
                    Icon(
                      AppTheme.categoryIcon(cat),
                      size: 13,
                      color: isSelected ? Colors.white : color,
                    ),
                    const SizedBox(width: 5),
                  ],
                  Text(
                    cat,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: isSelected ? Colors.white : AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
