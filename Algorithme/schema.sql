-- public.settings definition

-- Drop table

-- DROP TABLE public.settings;

CREATE TABLE public.settings (
	preset_name varchar NULL,
	like_scale float4 DEFAULT 1 NOT NULL,
	view_scale float4 DEFAULT 0.1 NOT NULL,
	tags_scale float4 DEFAULT 2 NOT NULL,
	like_min float4 DEFAULT '-100'::integer NOT NULL,
	like_max float4 DEFAULT 100 NOT NULL,
	view_min float4 DEFAULT '-100'::integer NOT NULL,
	view_max float4 DEFAULT 100 NOT NULL,
	tags_min float4 DEFAULT '-100'::integer NOT NULL,
	tags_max float4 DEFAULT 100 NOT NULL,
	has_already_been_seen_scale float4 DEFAULT 1 NOT NULL,
	has_already_been_seen_min float4 DEFAULT '-100'::integer NOT NULL,
	has_already_been_seen_max float4 DEFAULT 100 NOT NULL,
	is_following_scale float4 DEFAULT 1 NOT NULL,
	is_following_min float4 DEFAULT '-100'::integer NOT NULL,
	is_following_max float4 DEFAULT 100 NOT NULL,
	settings_pk serial4 NOT NULL,
	CONSTRAINT settings_pk PRIMARY KEY (settings_pk)
);


-- public.tags definition

-- Drop table

-- DROP TABLE public.tags;

CREATE TABLE public.tags (
	tags varchar NOT NULL,
	CONSTRAINT tags_pk PRIMARY KEY (tags)
);


-- public.users definition

-- Drop table

-- DROP TABLE public.users;

CREATE TABLE public.users (
	username varchar NOT NULL,
	user_pk serial4 NOT NULL,
	"password" varchar NULL,
	register_date date NULL,
	email_adress varchar NULL,
	channel_url varchar NULL,
	is_youtube_user bool NULL,
	can_update_channel bool DEFAULT false NOT NULL,
	can_add_youtube_video bool DEFAULT false NOT NULL,
	can_update_all_videos_from_all_channels bool DEFAULT false NOT NULL,
	active_settings_pk int4 DEFAULT 1 NOT NULL,
	CONSTRAINT users_pk PRIMARY KEY (user_pk),
	CONSTRAINT active_settings_fk FOREIGN KEY (active_settings_pk) REFERENCES public.settings(settings_pk)
);


-- public.videos definition

-- Drop table

-- DROP TABLE public.videos;

CREATE TABLE public.videos (
	videourl varchar NOT NULL,
	user_pk int4 NULL,
	is_hidden bool DEFAULT false NOT NULL,
	first_upload date NULL,
	is_youtube_video bool DEFAULT false NULL,
	youtube_views int8 DEFAULT 0 NOT NULL,
	youtube_likes int8 DEFAULT 0 NOT NULL,
	latest_stat_update date DEFAULT CURRENT_DATE NULL,
	CONSTRAINT videos_pk PRIMARY KEY (videourl),
	CONSTRAINT videos_users_fk FOREIGN KEY (user_pk) REFERENCES public.users(user_pk)
);


-- public."comments" definition

-- Drop table

-- DROP TABLE public."comments";

CREATE TABLE public."comments" (
	videourl varchar NOT NULL,
	"content" varchar NOT NULL,
	user_pk int4 NOT NULL,
	comment_pk serial4 NOT NULL,
	"date" date DEFAULT CURRENT_DATE NULL,
	CONSTRAINT comments_pk PRIMARY KEY (comment_pk),
	CONSTRAINT comments_users_fk FOREIGN KEY (user_pk) REFERENCES public.users(user_pk),
	CONSTRAINT comments_videos_fk FOREIGN KEY (videourl) REFERENCES public.videos(videourl)
);


-- public.follow_tags definition

-- Drop table

-- DROP TABLE public.follow_tags;

CREATE TABLE public.follow_tags (
	user_pk int4 NULL,
	tags varchar NULL,
	CONSTRAINT follow_tags_tags_fk FOREIGN KEY (tags) REFERENCES public.tags(tags),
	CONSTRAINT follow_tags_users_fk FOREIGN KEY (user_pk) REFERENCES public.users(user_pk)
);


-- public.has_been_liked_by definition

-- Drop table

-- DROP TABLE public.has_been_liked_by;

CREATE TABLE public.has_been_liked_by (
	videourl varchar NULL,
	user_pk int4 NULL,
	is_dislike bool NULL,
	CONSTRAINT has_been_liked_by_unique UNIQUE (videourl, user_pk, is_dislike),
	CONSTRAINT has_been_liked_by_users_fk FOREIGN KEY (user_pk) REFERENCES public.users(user_pk),
	CONSTRAINT has_been_liked_by_videos_fk FOREIGN KEY (videourl) REFERENCES public.videos(videourl)
);


-- public.has_been_viewed_by definition

-- Drop table

-- DROP TABLE public.has_been_viewed_by;

CREATE TABLE public.has_been_viewed_by (
	videourl varchar NULL,
	user_pk int4 NULL,
	CONSTRAINT has_been_viewed_by_users_fk FOREIGN KEY (user_pk) REFERENCES public.users(user_pk),
	CONSTRAINT has_been_viewed_by_videos_fk FOREIGN KEY (videourl) REFERENCES public.videos(videourl)
);


-- public.has_settings_preset definition

-- Drop table

-- DROP TABLE public.has_settings_preset;

CREATE TABLE public.has_settings_preset (
	user_pk int4 NOT NULL,
	settings_pk int4 NOT NULL,
	CONSTRAINT has_settings_preset_settings_fk FOREIGN KEY (settings_pk) REFERENCES public.settings(settings_pk),
	CONSTRAINT has_settings_preset_users_fk FOREIGN KEY (user_pk) REFERENCES public.users(user_pk)
);


-- public.has_tag definition

-- Drop table

-- DROP TABLE public.has_tag;

CREATE TABLE public.has_tag (
	videourl varchar NULL,
	tags varchar NULL,
	CONSTRAINT has_tag_tags_fk FOREIGN KEY (tags) REFERENCES public.tags(tags),
	CONSTRAINT has_tag_videos_fk FOREIGN KEY (videourl) REFERENCES public.videos(videourl)
);


-- public.is_following definition

-- Drop table

-- DROP TABLE public.is_following;

CREATE TABLE public.is_following (
	follower_pk int4 NOT NULL,
	followed_pk int4 NOT NULL,
	CONSTRAINT is_following_unique UNIQUE (follower_pk, followed_pk),
	CONSTRAINT followed_fk FOREIGN KEY (followed_pk) REFERENCES public.users(user_pk),
	CONSTRAINT follower_fk FOREIGN KEY (follower_pk) REFERENCES public.users(user_pk)
);