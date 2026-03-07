// lib/models/search_result_model.dart

class SearchResultItem {
  final String id;
  final String name;
  final String type; // 'college' | 'community'
  final double score;
  final String? contactEmail;
  final String? physicalAddress;
  final int? communityCount;
  final String? communityType; // 'PUBLIC' | 'PRIVATE'
  final List<String>? parentColleges;
  final int? memberCount;

  const SearchResultItem({
    required this.id,
    required this.name,
    required this.type,
    required this.score,
    this.contactEmail,
    this.physicalAddress,
    this.communityCount,
    this.communityType,
    this.parentColleges,
    this.memberCount,
  });

  factory SearchResultItem.fromMap(Map<String, dynamic> map) {
    return SearchResultItem(
      id: map['id'] as String,
      name: map['name'] as String,
      type: map['type'] as String,
      score: (map['score'] as num).toDouble(),
      contactEmail: map['contact_email'] as String?,
      physicalAddress: map['physical_address'] as String?,
      communityCount: map['community_count'] as int?,
      communityType: map['community_type'] as String?,
      parentColleges: (map['parent_colleges'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      memberCount: map['member_count'] as int?,
    );
  }
}

class SearchResponse {
  final String query;
  final String typeFilter;
  final List<SearchResultItem> items;
  final int total;
  final int page;
  final int pageSize;

  const SearchResponse({
    required this.query,
    required this.typeFilter,
    required this.items,
    required this.total,
    required this.page,
    required this.pageSize,
  });

  factory SearchResponse.fromMap(Map<String, dynamic> map) {
    return SearchResponse(
      query: map['query'] as String,
      typeFilter: map['type_filter'] as String,
      items: (map['items'] as List<dynamic>)
          .map((e) => SearchResultItem.fromMap(e as Map<String, dynamic>))
          .toList(),
      total: map['total'] as int,
      page: map['page'] as int,
      pageSize: map['page_size'] as int,
    );
  }
}
