def mongodb2():
    return """
MongoDB Exercise: Library Management System

1️⃣ Database and Collections
use LibraryDB;

db.books.insertMany([
  {
    title: "The Great Gatsby",
    author: "F. Scott Fitzgerald",
    genre: ["Classic", "Fiction"],
    published_year: 1925,
    publisher: "Scribner",
    copies_available: 3,
    total_copies: 5,
    borrowers: [
      {
        uuid: "u1001",
        borrow_date: ISODate("2023-01-15"),
        due_date: ISODate("2023-02-15")
      }
    ]
  },
  {
    title: "To Kill a Mockingbird",
    author: "Harper Lee",
    genre: ["Classic", "Novel"],
    published_year: 1960,
    publisher: "J.B. Lippincott & Co.",
    copies_available: 2,
    total_copies: 4,
    borrowers: []
  }
]);

db.users.insertMany([
  {
    uuid: "u1001",
    name: "John Smith",
    email: "johnsmith@example.com",
    membership_type: "premium",
    join_date: ISODate("2022-05-10"),
    books_borrowed: 4,
    fine: 0
  },
  {
    uuid: "u1002",
    name: "Alice Johnson",
    email: "alicej@example.com",
    membership_type: "regular",
    join_date: ISODate("2023-01-12"),
    books_borrowed: 1,
    fine: 20
  }
]);

2️⃣ Queries
db.books.find({ published_year: { $gt: 1950 } });
db.books.find({ copies_available: { $gte: 2 } });
db.books.find({ genre: "Classic" });
db.books.find({ "borrowers.uuid": "u1001" });
db.books.countDocuments();

3️⃣ Updates
db.books.updateOne(
  { title: "The Great Gatsby" },
  {
    $push: {
      borrowers: {
        uuid: "u1002",
        borrow_date: ISODate("2023-03-01"),
        due_date: ISODate("2023-03-30")
      }
    }
  }
);

db.books.updateOne(
  { title: "To Kill a Mockingbird" },
  { $inc: { copies_available: 1 } }
);

db.users.updateOne(
  { uuid: "u1002" },
  { $set: { membership_type: "premium" } }
);

db.books.updateMany(
  { published_year: { $lt: 1970 } },
  { $addToSet: { genre: "Novel" } }
);

db.books.updateOne(
  { title: "The Great Gatsby" },
  { $pull: { borrowers: { uuid: "u1001" } } }
);

4️⃣ Aggregation
db.books.aggregate([{ $group: { _id: null, avgCopies: { $avg: "$total_copies" } } }]);
db.books.aggregate([{ $group: { _id: "$publisher", totalBooks: { $sum: 1 } } }]);
db.books.aggregate([
  { $project: { title: 1, borrow_count: { $size: "$borrowers" } } },
  { $sort: { borrow_count: 1 } },
  { $limit: 3 }
]);
db.users.aggregate([{ $group: { _id: null, totalFines: { $sum: "$fine" } } }]);
db.users.find({ books_borrowed: { $gte: 1 } });

5️⃣ Indexing
db.books.createIndex({ isbn: 1 });
db.books.createIndex({ author: 1, published_year: -1 });
db.books.createIndex({ title: "text" });
db.books.createIndex({ genre: 1 });
"""
