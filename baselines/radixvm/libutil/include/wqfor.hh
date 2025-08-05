// Default copy_value
template <typename T>
static inline T
copy_value(T &it)
{
  return it;
}

// Default free_value
template <typename T>
static inline void
free_value(T &it, T &v)
{
}

template <typename IT, typename BODY>
struct forwork : public work {
  forwork(IT &it, bool (*cond)(IT &it), BODY &body, wframe &frame) 
    : it_(it), cond_(cond), body_(body), frame_(frame) {}

  void run() override {
    decltype(copy_value(it_)) v = copy_value(it_);
    ++it_;
    if (cond_(it_)) {
      forwork<IT, BODY> *w = new forwork<IT, BODY>(it_, cond_, body_, frame_);
      frame_.inc();
      wq_push(w);    
    }
    body_(v);
    free_value(it_, v);
    frame_.dec();
    delete this;
  }

  static void* operator new(unsigned long nbytes) {
    assert(nbytes == sizeof(forwork<IT, BODY>));
    return xallocwork(sizeof(forwork));
  }

  static void operator delete(void*p) {
    xfreework(p, sizeof(forwork));
  }

  IT &it_;
  bool (*cond_)(IT&);
  BODY &body_;
  wframe &frame_;
};

template <typename IT, typename BODY>
static inline void
wq_for(IT &init, bool (*cond)(IT &it), BODY body)
{
  wframe frame(0);

  // XXX(sbw) should be able to coarsen loop

  if (!cond(init))
    return;

  decltype(copy_value(init)) v = copy_value(init);
  ++init;
  if (cond(init)) {
    forwork<IT, BODY> *w = new forwork<IT, BODY>(init, cond, body, frame);
    frame.inc();
    wq_push(w);
  }

  body(v);
  free_value(init, v);

  while (!frame.zero())
    wq_trywork();
}

// For debugging
// Same API as wq_for but serially executes body 
template <typename IT, typename BODY>
static inline void
wq_for_serial(IT &init, bool (*cond)(IT &it), BODY body)
{
  for (; cond(init); ++init) {
    decltype(copy_value(init)) v = copy_value(init);
    body(v);
    free_value(init, v);
  }
}
