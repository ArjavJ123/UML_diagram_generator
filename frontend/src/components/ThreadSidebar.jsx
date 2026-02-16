const ThreadSidebar = ({
  threads,
  currentThread,
  setCurrentThread,
  createNewThread,
}) => {
  return (
    <div className="sidebar">
      <button onClick={createNewThread}>+ New Thread</button>

      {threads.map((thread) => (
        <div
          key={thread}
          className={thread === currentThread ? "active-thread" : ""}
          onClick={() => setCurrentThread(thread)}
        >
          {thread}
        </div>
      ))}
    </div>
  );
};

export default ThreadSidebar;
