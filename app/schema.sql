create table user(
    id text primary key,
    display_name text not null,
    created_at datetime not null default current_timestamp
);

create table genre(
    id integer primary key autoincrement,
    name text not null,
    user_id text references user (id) on delete cascade
);

create table method(
    id integer primary key autoincrement,
    name text not null,
    not_own integer not null default 0,
    user_id text references user (id) on delete cascade
);

create table payment(
    id integer primary key autoincrement,
    amount integer not null,
    date date not null,
    shop text not null,
    genre integer references genre (id) on delete set null,
    attr text,
    note text,
    method integer references method (id) on delete set null,
    user_id text references user (id) on delete cascade
);

insert into genre("name") values ("食費"), ("日用品"), ("交通費"), ("趣味・娯楽"), ("光熱費");
insert into method("name") values ("現金");