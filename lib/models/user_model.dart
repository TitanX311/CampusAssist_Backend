// models/user_model.dart

class UserModel {
  final String id;
  final String name;
  final String email;
  final String? pictureURL;
  final String? college;
  final bool emailVerified;
  final String userType; // 'USER' | 'COLLEGE' | 'SUPER_ADMIN'
  final String refreshToken;
  final String accessToken;

  factory UserModel.fromResponse(Map<String, dynamic> map) {
    return UserModel(
      id: map['id'] ?? '',
      name: map['name'] ?? '',
      email: map['email'] ?? '',
      pictureURL: map['picture'],
      college: map['college'],
      emailVerified: map['email_verified'] as bool? ?? false,
      userType: map['type'] as String? ?? 'USER',
      refreshToken: map['refresh_token'] ?? '',
      accessToken: map['access_token'] ?? '',
    );
  }

  //<editor-fold desc="Data Methods">
  const UserModel({
    required this.id,
    required this.name,
    required this.email,
    this.pictureURL,
    this.college,
    this.emailVerified = false,
    this.userType = 'USER',
    required this.refreshToken,
    required this.accessToken,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is UserModel &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          name == other.name &&
          email == other.email &&
          pictureURL == other.pictureURL &&
          college == other.college &&
          emailVerified == other.emailVerified &&
          userType == other.userType &&
          refreshToken == other.refreshToken &&
          accessToken == other.accessToken);

  @override
  int get hashCode =>
      id.hashCode ^
      name.hashCode ^
      email.hashCode ^
      pictureURL.hashCode ^
      college.hashCode ^
      emailVerified.hashCode ^
      userType.hashCode ^
      refreshToken.hashCode ^
      accessToken.hashCode;

  @override
  String toString() {
    return 'UserModel{'
        ' id: $id,'
        ' name: $name,'
        ' email: $email,'
        ' pictureURL: $pictureURL,'
        ' college: $college,'
        ' emailVerified: $emailVerified,'
        ' userType: $userType,'
        ' refreshToken: $refreshToken,'
        ' accessToken: $accessToken,'
        '}';
  }

  UserModel copyWith({
    String? id,
    String? name,
    String? email,
    String? pictureURL,
    String? college,
    bool? emailVerified,
    String? userType,
    String? refreshToken,
    String? accessToken,
  }) {
    return UserModel(
      id: id ?? this.id,
      name: name ?? this.name,
      email: email ?? this.email,
      pictureURL: pictureURL ?? this.pictureURL,
      college: college ?? this.college,
      emailVerified: emailVerified ?? this.emailVerified,
      userType: userType ?? this.userType,
      refreshToken: refreshToken ?? this.refreshToken,
      accessToken: accessToken ?? this.accessToken,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'pictureURL': pictureURL,
      'college': college,
      'emailVerified': emailVerified,
      'userType': userType,
      'refreshToken': refreshToken,
      'accessToken': accessToken,
    };
  }

  factory UserModel.fromMap(Map<String, dynamic> map) {
    return UserModel(
      id: map['id'] as String,
      name: map['name'] as String? ?? '',
      email: map['email'] as String,
      pictureURL: map['pictureURL'] as String?,
      college: map['college'] as String?,
      emailVerified: map['emailVerified'] as bool? ?? false,
      userType: map['userType'] as String? ?? 'USER',
      refreshToken: map['refreshToken'] as String? ?? '',
      accessToken: map['accessToken'] as String? ?? '',
    );
  }

  //</editor-fold>
}
