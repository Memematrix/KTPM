-- ============================================================
-- HỆ THỐNG BÁN VÉ XEM PHIM — SCHEMA HOÀN CHỈNH (Supabase/Postgres)
-- Bao gồm: fix các lỗi đã review, indexes, triggers, RLS, seed data
-- Chạy toàn bộ file này trong Supabase SQL Editor (role postgres)
-- ============================================================

-- ============================================================
-- PART 0: EXTENSIONS
-- ============================================================
create extension if not exists "uuid-ossp";
create extension if not exists "btree_gist";   -- cần cho exclusion constraint chống trùng suất chiếu
create extension if not exists "pgcrypto";     -- cần để hash mật khẩu khi seed auth.users

-- ============================================================
-- PART 1: TABLES
-- ============================================================

-- 1. Users
create table public.users (
  id uuid references auth.users not null primary key,
  name text not null,
  phone text,
  role text default 'customer' check (role in ('admin', 'customer')),
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Movies
create table public.movies (
  id uuid default uuid_generate_v4() primary key,
  title text not null,
  description text,
  duration integer not null check (duration > 0),
  release_date date,
  poster_url text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Screens
create table public.screens (
  id uuid default uuid_generate_v4() primary key,
  name text not null,
  total_seats integer not null default 0 -- được đồng bộ tự động bằng trigger, không insert tay
);

-- 4. Seats
create table public.seats (
  id uuid default uuid_generate_v4() primary key,
  screen_id uuid references public.screens(id) on delete cascade not null,
  row_letter varchar(2) not null,
  seat_number integer not null,
  type text default 'standard' check (type in ('standard', 'vip', 'sweetbox')),
  -- FIX: chống tạo trùng ghế vật lý trong cùng 1 phòng
  unique (screen_id, row_letter, seat_number)
);

-- 5. Showtimes
create table public.showtimes (
  id uuid default uuid_generate_v4() primary key,
  movie_id uuid references public.movies(id) on delete cascade not null,
  screen_id uuid references public.screens(id) on delete cascade not null,
  start_time timestamp with time zone not null,
  end_time timestamp with time zone not null,
  base_price numeric(10,2) not null check (base_price >= 0),
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  -- FIX: đảm bảo giờ kết thúc sau giờ bắt đầu
  constraint end_after_start check (end_time > start_time),

    exclude using gist (
    screen_id with =,
    tstzrange(start_time, end_time) with &&
  )
);

-- 6. Food
create table public.food (
  id uuid default uuid_generate_v4() primary key,
  name text not null,
  description text,
  price numeric(10,2) not null check (price >= 0),
  image_url text
);

-- 7. Orders
create table public.orders (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.users(id) not null,
  total_amount numeric(10,2) not null default 0, -- được tính tự động bằng trigger
  status text default 'pending' check (status in ('pending', 'completed', 'cancelled')),
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 8. Tickets
create table public.tickets (
  id uuid default uuid_generate_v4() primary key,
  order_id uuid references public.orders(id) on delete cascade not null,
  showtime_id uuid references public.showtimes(id) not null,
  seat_id uuid references public.seats(id) not null,
  price numeric(10,2) not null check (price >= 0),
  -- FIX: hỗ trợ giữ ghế tạm thời (seat holding) trong lúc thanh toán
  status text default 'pending' check (status in ('pending', 'confirmed', 'cancelled')),
  expires_at timestamp with time zone, -- hạn giữ ghế, null nếu đã confirmed
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- FIX: chỉ chống trùng ghế đối với vé đang "sống" (pending/confirmed).
-- Vé đã cancelled thì ghế được thả ra cho người khác đặt lại.
create unique index tickets_active_seat_unique
  on public.tickets (showtime_id, seat_id)
  where status in ('pending', 'confirmed');

-- 9. Order_Food
create table public.order_food (
  order_id uuid references public.orders(id) on delete cascade not null,
  food_id uuid references public.food(id) not null,
  quantity integer not null default 1 check (quantity > 0),
  price numeric(10,2) not null check (price >= 0),
  primary key (order_id, food_id)
);

-- 10. Reviews
create table public.reviews (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.users(id) on delete cascade not null,
  movie_id uuid references public.movies(id) on delete cascade not null,
  rating integer check (rating >= 1 and rating <= 5) not null,
  comment text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- ============================================================
-- PART 2: INDEXES (Postgres không tự tạo index cho FK)
-- ============================================================
create index idx_showtimes_movie   on public.showtimes (movie_id);
create index idx_showtimes_screen  on public.showtimes (screen_id);
create index idx_seats_screen      on public.seats (screen_id);
create index idx_tickets_order     on public.tickets (order_id);
create index idx_tickets_showtime  on public.tickets (showtime_id);
create index idx_tickets_seat      on public.tickets (seat_id);
create index idx_orders_user       on public.orders (user_id);
create index idx_order_food_food   on public.order_food (food_id);
create index idx_reviews_movie     on public.reviews (movie_id);
create index idx_reviews_user      on public.reviews (user_id);

-- ============================================================
-- PART 3: FUNCTIONS & TRIGGERS
-- ============================================================

-- 3.1 Cập nhật updated_at tự động
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$ language plpgsql;

create trigger trg_orders_updated_at
before update on public.orders
for each row execute function public.set_updated_at();

create trigger trg_showtimes_updated_at
before update on public.showtimes
for each row execute function public.set_updated_at();

-- 3.2 FIX: đồng bộ screens.total_seats theo số ghế thực tế
create or replace function public.sync_screen_total_seats()
returns trigger as $$
declare
  target_screen_id uuid;
begin
  target_screen_id := coalesce(new.screen_id, old.screen_id);
  update public.screens
  set total_seats = (select count(*) from public.seats where screen_id = target_screen_id)
  where id = target_screen_id;
  return coalesce(new, old);
end;
$$ language plpgsql;

create trigger trg_sync_total_seats
after insert or update or delete on public.seats
for each row execute function public.sync_screen_total_seats();

-- 3.3 FIX: tự tính lại orders.total_amount mỗi khi tickets/order_food thay đổi
create or replace function public.recalc_order_total()
returns trigger as $$
declare
  target_order_id uuid;
begin
  target_order_id := coalesce(new.order_id, old.order_id);

  update public.orders
  set total_amount = (
    coalesce((select sum(price) from public.tickets
              where order_id = target_order_id and status = 'confirmed'), 0)
    +
    coalesce((select sum(price * quantity) from public.order_food
              where order_id = target_order_id), 0)
  )
  where id = target_order_id;

  return coalesce(new, old);
end;
$$ language plpgsql;

create trigger trg_recalc_total_tickets
after insert or update or delete on public.tickets
for each row execute function public.recalc_order_total();

create trigger trg_recalc_total_food
after insert or update or delete on public.order_food
for each row execute function public.recalc_order_total();

-- 3.4 FIX: dọn các ghế "giữ chỗ" (pending) đã hết hạn -> nhả ghế
create or replace function public.release_expired_seat_holds()
returns void as $$
begin
  update public.tickets
  set status = 'cancelled'
  where status = 'pending' and expires_at is not null and expires_at < now();
end;
$$ language plpgsql;

-- Nếu project có bật extension pg_cron, chạy dòng dưới (bỏ comment) để tự động
-- gọi hàm dọn ghế hết hạn mỗi phút:
-- select cron.schedule('release-expired-holds', '* * * * *',
--   $$select public.release_expired_seat_holds();$$);

-- ============================================================
-- PART 4: ROW LEVEL SECURITY (bắt buộc với Supabase)
-- ============================================================

create or replace function public.is_admin()
returns boolean as $$
  select exists (
    select 1 from public.users where id = auth.uid() and role = 'admin'
  );
$$ language sql stable security definer;

alter table public.users       enable row level security;
alter table public.movies      enable row level security;
alter table public.screens     enable row level security;
alter table public.seats       enable row level security;
alter table public.showtimes   enable row level security;
alter table public.food        enable row level security;
alter table public.orders      enable row level security;
alter table public.tickets     enable row level security;
alter table public.order_food  enable row level security;
alter table public.reviews     enable row level security;

-- Users
create policy "users_select_own_or_admin" on public.users
  for select using (auth.uid() = id or public.is_admin());
create policy "users_update_own" on public.users
  for update using (auth.uid() = id) with check (auth.uid() = id);
create policy "users_admin_all" on public.users
  for all using (public.is_admin());

-- Dữ liệu công khai (đọc tự do, ghi chỉ admin)
create policy "movies_public_read"   on public.movies   for select using (true);
create policy "movies_admin_write"   on public.movies   for all    using (public.is_admin());
create policy "screens_public_read"  on public.screens  for select using (true);
create policy "screens_admin_write"  on public.screens  for all    using (public.is_admin());
create policy "seats_public_read"    on public.seats    for select using (true);
create policy "seats_admin_write"    on public.seats    for all    using (public.is_admin());
create policy "showtimes_public_read" on public.showtimes for select using (true);
create policy "showtimes_admin_write" on public.showtimes for all    using (public.is_admin());
create policy "food_public_read"     on public.food     for select using (true);
create policy "food_admin_write"     on public.food     for all    using (public.is_admin());

-- Orders
create policy "orders_select_own_or_admin" on public.orders
  for select using (auth.uid() = user_id or public.is_admin());
create policy "orders_insert_own" on public.orders
  for insert with check (auth.uid() = user_id);
create policy "orders_admin_all" on public.orders
  for all using (public.is_admin());

-- Tickets (qua quan hệ với orders)
create policy "tickets_select_own_or_admin" on public.tickets
  for select using (
    exists (select 1 from public.orders o where o.id = tickets.order_id
            and (o.user_id = auth.uid() or public.is_admin()))
  );
create policy "tickets_insert_own" on public.tickets
  for insert with check (
    exists (select 1 from public.orders o where o.id = tickets.order_id and o.user_id = auth.uid())
  );
create policy "tickets_admin_all" on public.tickets
  for all using (public.is_admin());

-- Order_food (qua quan hệ với orders)
create policy "order_food_select_own_or_admin" on public.order_food
  for select using (
    exists (select 1 from public.orders o where o.id = order_food.order_id
            and (o.user_id = auth.uid() or public.is_admin()))
  );
create policy "order_food_insert_own" on public.order_food
  for insert with check (
    exists (select 1 from public.orders o where o.id = order_food.order_id and o.user_id = auth.uid())
  );
create policy "order_food_admin_all" on public.order_food
  for all using (public.is_admin());

-- Reviews
create policy "reviews_public_read" on public.reviews for select using (true);
create policy "reviews_insert_own"  on public.reviews for insert with check (auth.uid() = user_id);
create policy "reviews_update_own"  on public.reviews for update using (auth.uid() = user_id);
create policy "reviews_delete_own"  on public.reviews for delete using (auth.uid() = user_id);
create policy "reviews_admin_all"   on public.reviews for all using (public.is_admin());

-- ============================================================
-- PART 5: SEED DATA — đủ các tình huống thực tế để code demo
-- ============================================================

-- 5.1 Auth users (chỉ để demo — trong thực tế user được tạo qua Supabase Auth API)
insert into auth.users (
  instance_id, id, aud, role, email, encrypted_password,
  email_confirmed_at, created_at, updated_at,
  raw_app_meta_data, raw_user_meta_data
) values
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000001',
   'authenticated', 'authenticated', 'admin@cinema.vn', crypt('Admin@123', gen_salt('bf')),
   now(), now(), now(), '{"provider":"email","providers":["email"]}', '{}'),
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000002',
   'authenticated', 'authenticated', 'vana@gmail.com', crypt('User@123', gen_salt('bf')),
   now(), now(), now(), '{"provider":"email","providers":["email"]}', '{}'),
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000003',
   'authenticated', 'authenticated', 'thib@gmail.com', crypt('User@123', gen_salt('bf')),
   now(), now(), now(), '{"provider":"email","providers":["email"]}', '{}'),
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000004',
   'authenticated', 'authenticated', 'vanc@gmail.com', crypt('User@123', gen_salt('bf')),
   now(), now(), now(), '{"provider":"email","providers":["email"]}', '{}')
on conflict (id) do nothing;

-- 5.2 Public users
insert into public.users (id, name, phone, role) values
  ('a0000000-0000-0000-0000-000000000001', 'Quản Trị Viên',   '0900000001', 'admin'),
  ('a0000000-0000-0000-0000-000000000002', 'Nguyễn Văn A',    '0900000002', 'customer'),
  ('a0000000-0000-0000-0000-000000000003', 'Trần Thị B',      '0900000003', 'customer'),
  ('a0000000-0000-0000-0000-000000000004', 'Lê Văn C',        '0900000004', 'customer');

-- 5.3 Movies (đủ trường hợp: có/thiếu mô tả, có/thiếu poster, phim sắp chiếu chưa có suất)
insert into public.movies (id, title, description, duration, release_date, poster_url) values
  ('10000000-0000-0000-0000-000000000001', 'Địa Đạo: Mặt Trời Trong Bóng Tối',
   'Phim lịch sử - chiến tranh Việt Nam.', 128, '2025-04-04', 'https://example.com/poster1.jpg'),
  ('10000000-0000-0000-0000-000000000002', 'Mai',
   'Phim tâm lý - tình cảm.', 131, '2024-02-10', 'https://example.com/poster2.jpg'),
  ('10000000-0000-0000-0000-000000000003', 'Lật Mặt 7: Một Điều Ước',
   'Phim hài - gia đình.', 140, '2024-04-26', 'https://example.com/poster3.jpg'),
  ('10000000-0000-0000-0000-000000000004', 'Exhuma: Quật Mộ Trùng Ma',
   null, 134, '2024-03-01', null), -- edge case: thiếu mô tả và poster
  ('10000000-0000-0000-0000-000000000005', 'Godzilla x Kong: Đế Chế Mới',
   'Phim quái vật - hành động (sắp chiếu, chưa có suất chiếu nào).', 115, '2026-11-01', 'https://example.com/poster5.jpg');

-- 5.4 Screens
insert into public.screens (id, name) values
  ('20000000-0000-0000-0000-000000000001', 'Phòng 1 - Standard/VIP/Sweetbox'),
  ('20000000-0000-0000-0000-000000000002', 'Phòng 2 - Standard/VIP');

-- 5.5 Seats — Phòng 1: A-D standard (8 ghế/hàng), E vip (8 ghế), F sweetbox (4 ghế đôi)
insert into public.seats (screen_id, row_letter, seat_number, type)
select
    '20000000-0000-0000-0000-000000000001'::uuid,
    chr(64 + r),
    s,
    'standard'
from generate_series(1, 4) r,
     generate_series(1, 8) s
union all
select
    '20000000-0000-0000-0000-000000000001'::uuid,
    'E',
    s,
    'vip'
from generate_series(1, 8) s
union all
select
    '20000000-0000-0000-0000-000000000001'::uuid,
    'F',
    s,
    'sweetbox'
from generate_series(1, 4) s;

-- Seats — Phòng 2: A-C standard (8 ghế/hàng), D vip (6 ghế)
insert into public.seats (screen_id, row_letter, seat_number, type)
select
    '20000000-0000-0000-0000-000000000002'::uuid,
    chr(64 + r),
    s,
    'standard'
from generate_series(1, 3) r,
     generate_series(1, 8) s
union all
select
    '20000000-0000-0000-0000-000000000002'::uuid,
    'D',
    s,
    'vip'
from generate_series(1, 6) s;

-- 5.6 Food
insert into public.food (id, name, description, price, image_url) values
  ('30000000-0000-0000-0000-000000000001', 'Bắp rang bơ (lớn)', 'Bắp rang bơ size lớn', 55000, 'https://example.com/food1.jpg'),
  ('30000000-0000-0000-0000-000000000002', 'Combo bắp nước đôi', '2 bắp + 2 nước ngọt', 99000, 'https://example.com/food2.jpg'),
  ('30000000-0000-0000-0000-000000000003', 'Coca Cola (lớn)', null, 35000, null),
  ('30000000-0000-0000-0000-000000000004', 'Nachos phô mai', 'Nachos kèm sốt phô mai', 65000, 'https://example.com/food4.jpg');

-- 5.7 Showtimes (đủ trường hợp: quá khứ, hôm nay, tương lai; không có suất chồng giờ)
insert into public.showtimes (id, movie_id, screen_id, start_time, end_time, base_price) values
  -- Suất đã chiếu xong (để test order completed + review)
  ('40000000-0000-0000-0000-000000000001',
   '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001',
   now() - interval '2 days' + time '19:00', now() - interval '2 days' + time '21:10', 75000),
  -- Suất hôm nay
  ('40000000-0000-0000-0000-000000000002',
   '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002',
   date_trunc('day', now()) + interval '20 hours', date_trunc('day', now()) + interval '22 hours 15 minutes', 80000),
  -- Suất tương lai (ngày mai) - phòng 1, khác giờ với suất đã chiếu -> không vi phạm exclusion constraint
  ('40000000-0000-0000-0000-000000000003',
   '10000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000001',
   now() + interval '1 day' + time '18:00', now() + interval '1 day' + time '20:20', 85000),
  -- Suất tương lai khác cho phòng 1 cùng ngày nhưng khác khung giờ (chứng minh không chồng)
  ('40000000-0000-0000-0000-000000000004',
   '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001',
   now() + interval '1 day' + time '21:00', now() + interval '1 day' + time '23:10', 75000),
  -- Suất tương lai phòng 2
  ('40000000-0000-0000-0000-000000000005',
   '10000000-0000-0000-0000-000000000004', '20000000-0000-0000-0000-000000000002',
   now() + interval '2 days' + time '19:30', now() + interval '2 days' + time '21:45', 80000);
  -- Lưu ý: phim "Godzilla x Kong" (id ...0005) CHƯA có suất chiếu nào — đúng nghiệp vụ "phim sắp chiếu"

-- 5.8 Orders + Tickets + Order_food (các tình huống thực tế)

-- Order 1: Nguyễn Văn A — ĐÃ HOÀN TẤT, xem suất quá khứ, có vé + đồ ăn
insert into public.orders (id, user_id, status) values
  ('50000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000002', 'completed');

insert into public.tickets (order_id, showtime_id, seat_id, price, status)
select '50000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', id, 75000, 'confirmed'
from public.seats where screen_id = '20000000-0000-0000-0000-000000000001' and row_letter = 'A' and seat_number in (1,2);

insert into public.order_food (order_id, food_id, quantity, price) values
  ('50000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000002', 1, 99000);

-- Order 2: Trần Thị B — ĐÃ HOÀN TẤT, ghế VIP cho suất tương lai, không mua đồ ăn
insert into public.orders (id, user_id, status) values
  ('50000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000003', 'completed');

insert into public.tickets (order_id, showtime_id, seat_id, price, status)
select '50000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000003', id, 85000 + 20000, 'confirmed'
from public.seats where screen_id = '20000000-0000-0000-0000-000000000001' and row_letter = 'E' and seat_number = 4;

-- Order 3: Lê Văn C — ĐANG GIỮ GHẾ (pending), demo cơ chế seat-holding, hết hạn sau 10 phút
insert into public.orders (id, user_id, status) values
  ('50000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000004', 'pending');

insert into public.tickets (order_id, showtime_id, seat_id, price, status, expires_at)
select '50000000-0000-0000-0000-000000000003', '40000000-0000-0000-0000-000000000004', id, 75000, 'pending', now() + interval '10 minutes'
from public.seats where screen_id = '20000000-0000-0000-0000-000000000001' and row_letter = 'B' and seat_number = 5;

-- Order 4: Nguyễn Văn A — ĐÃ HỦY, ghế được nhả lại cho người khác đặt
insert into public.orders (id, user_id, status) values
  ('50000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000002', 'cancelled');

insert into public.tickets (order_id, showtime_id, seat_id, price, status)
select '50000000-0000-0000-0000-000000000004', '40000000-0000-0000-0000-000000000005', id, 80000, 'cancelled'
from public.seats where screen_id = '20000000-0000-0000-0000-000000000002' and row_letter = 'D' and seat_number = 1;

-- Order 5: Trần Thị B — CHỈ MUA ĐỒ ĂN, không có vé (edge case: mua bắp nước tại quầy, không xem phim)
insert into public.orders (id, user_id, status) values
  ('50000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000003', 'completed');

insert into public.order_food (order_id, food_id, quantity, price) values
  ('50000000-0000-0000-0000-000000000005', '30000000-0000-0000-0000-000000000001', 2, 55000),
  ('50000000-0000-0000-0000-000000000005', '30000000-0000-0000-0000-000000000003', 2, 35000);

-- 5.9 Reviews (có review đã xem thật, và 1 review "chưa xác thực" để thấy hệ thống hiện chưa ràng buộc điều này)
insert into public.reviews (user_id, movie_id, rating, comment) values
  ('a0000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', 5, 'Phim hay, cảm động, diễn xuất tốt.'),
  ('a0000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000003', 3, null), -- edge case: rating không kèm comment
  ('a0000000-0000-0000-0000-000000000004', '10000000-0000-0000-0000-000000000002', 4, 'Xem ké bạn kể lại thấy hay, để dành coi sau.'); -- chưa từng mua vé phim này

-- ============================================================
-- KIỂM TRA NHANH SAU KHI SEED
-- ============================================================
-- select * from public.orders;                 -- xem total_amount đã tự tính đúng chưa
-- select * from public.screens;                 -- xem total_seats đã tự đồng bộ (44 và 30)
-- select * from public.tickets where status='pending'; -- ghế đang giữ, còn hạn expires_at
-- select public.release_expired_seat_holds();   -- test hàm nhả ghế hết hạn


select * from public.users;

select * from public.movies;

select * from public.screens;

select * from public.seats;

select * from public.showtimes;
select * from public.food;
select * from public.orders;
select * from public.tickets;
select * from public.order_food;
select * from public.reviews;